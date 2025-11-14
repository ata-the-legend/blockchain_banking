"""Web3 client setup and blockchain utilities."""

import asyncio
from typing import Any, Dict
from functools import wraps

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import async_geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount

from app.settings import settings
from app.schemas.blockchain import BlockchainAccount
import structlog

logger = structlog.get_logger(__name__)


def async_retry(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for retrying async functions on failure.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "Retry attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e),
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "Max retries reached",
                            function=func.__name__,
                            error=str(e),
                        )
            raise last_exception

        return wrapper

    return decorator


class Web3Client:
    """Async Web3 client for blockchain interactions."""

    def __init__(self):
        """Initialize async Web3 client."""
        self.w3 = AsyncWeb3(AsyncHTTPProvider(settings.rpc_url))
        # Add middleware for PoA chains using async variant for AsyncWeb3
        self.w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
        self._connected = False

    async def connect(self) -> bool:
        """
        Verify connection to blockchain.

        Returns:
            bool: True if connected successfully
        """
        try:
            is_connected = await self.w3.is_connected()
            self._connected = is_connected
            if is_connected:
                logger.info(
                    "Connected to blockchain", rpc_url=settings.rpc_url
                )
            else:
                logger.error(
                    "Failed to connect to blockchain", rpc_url=settings.rpc_url
                )
            return is_connected
        except Exception as e:
            logger.error("Blockchain connection error", error=str(e))
            self._connected = False
            return False

    def get_contract(self, address: str):
        checksum_address = self.w3.to_checksum_address(address)
        return self.w3.eth.contract(
            address=checksum_address, abi=settings.erc20_abi
        )

    def create_account(self) -> BlockchainAccount:
        account: LocalAccount = Account.create()
        checksum_address = self.w3.to_checksum_address(account.address)
        private_key = account.key.hex()
        return BlockchainAccount(
            address=checksum_address, private_key=private_key
        )

    def get_account_from_key(self, private_key: str) -> LocalAccount:
        return Account.from_key(private_key)

    @async_retry(max_retries=3, delay=2.0)
    async def get_balance(self, address: str, token_address: str) -> int:
        contract = self.get_contract(token_address)
        checksum_address = self.w3.to_checksum_address(address)
        balance = await contract.functions.balanceOf(checksum_address).call()
        return balance

    @async_retry(max_retries=3, delay=2.0)
    async def get_native_balance(self, address: str) -> int:
        checksum_address = self.w3.to_checksum_address(address)
        balance = await self.w3.eth.get_balance(checksum_address)
        return balance

    @async_retry(max_retries=3, delay=2.0)
    async def estimate_gas(self, transaction: Dict[str, Any]) -> int:
        try:
            gas = await self.w3.eth.estimate_gas(transaction)
            # Add 20% buffer
            return int(gas * 1.2)
        except Exception as e:
            logger.warning(
                "Gas estimation failed, using default", error=str(e)
            )
            return settings.gas_limit

    @async_retry(max_retries=3, delay=2.0)
    async def send_native_token(
        self, from_private_key: str, to_address: str, amount_wei: int
    ) -> str:
        account = self.get_account_from_key(from_private_key)
        checksum_to = self.w3.to_checksum_address(to_address)

        nonce = await self.w3.eth.get_transaction_count(account.address)

        gas_price = self.w3.to_wei(settings.gas_price_gwei, "gwei")

        transaction = {
            "nonce": nonce,
            "to": checksum_to,
            "value": amount_wei,
            "gas": settings.gas_limit,
            "gasPrice": gas_price,
            "chainId": settings.chain_id,
        }

        transaction["gas"] = await self.estimate_gas(transaction)

        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, from_private_key
        )

        tx_hash = await self.w3.eth.send_raw_transaction(
            signed_txn.rawTransaction
        )
        tx_hash_hex = self.w3.to_hex(tx_hash)

        logger.info(
            "Native token sent",
            from_address=account.address,
            to_address=to_address,
            amount=amount_wei,
            tx_hash=tx_hash_hex,
        )

        receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise Exception(f"Transaction failed: {tx_hash_hex}")

        return tx_hash_hex

    @async_retry(max_retries=3, delay=2.0)
    async def transfer_erc20(
        self,
        from_private_key: str,
        to_address: str,
        amount: int,
        token_address: str,
    ) -> str:
        account = self.get_account_from_key(from_private_key)
        contract = self.get_contract(token_address)
        checksum_to = self.w3.to_checksum_address(to_address)

        nonce = await self.w3.eth.get_transaction_count(account.address)

        gas_price = self.w3.to_wei(settings.gas_price_gwei, "gwei")

        transaction = await contract.functions.transfer(
            checksum_to, amount
        ).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "gas": gas_price,
                "chainId": settings.chain_id,
            }
        )

        transaction["gas"] = await self.estimate_gas(transaction)

        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, from_private_key
        )

        tx_hash = await self.w3.eth.send_raw_transaction(
            signed_txn.rawTransaction
        )
        tx_hash_hex = self.w3.to_hex(tx_hash)

        logger.info(
            "ERC20 transfer sent",
            from_address=account.address,
            to_address=to_address,
            amount=amount,
            token=token_address,
            tx_hash=tx_hash_hex,
        )

        # Wait for transaction receipt
        receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise Exception(f"Transaction failed: {tx_hash_hex}")

        return tx_hash_hex


# Global Web3 client instance
web3_client = Web3Client()
