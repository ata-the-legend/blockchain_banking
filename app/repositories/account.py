"""Account repository with business logic for blockchain operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.utils.web3_client import web3_client
from app.settings import settings
from app.repositories.exceptions import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    InsufficientBalanceError,
    BlockchainError,
)
from app.schemas.user import UserResponse
import structlog

logger = structlog.get_logger(__name__)


class AccountRepository:
    """Repository for account management and blockchain operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_account(self, name: str) -> UserResponse:
        result = await self.db.execute(select(User).where(User.name == name))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning("Account already exists", name=name)
            raise AccountAlreadyExistsError(
                f"Account with name '{name}' already exists"
            )

        account_data = web3_client.create_account()

        # Create user in database
        user = User(
            name=name,
            address=account_data.address,
            private_key=account_data.private_key,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        faucet_tx_hash = await self.get_initial_fund(name, user)

        return UserResponse(
            name=user.name,
            address=user.address,
            private_key=user.private_key,
            faucet_tx_hash=faucet_tx_hash,
        )

    async def get_user_by_name(self, name: str) -> User:

        result = await self.db.execute(select(User).where(User.name == name))
        user = result.scalar_one_or_none()

        if not user:
            logger.warning("Account not found", name=name)
            raise AccountNotFoundError(f"Account '{name}' not found")

        return user

    async def get_balance(self, name: str, token_address: str) -> int:
        user = await self.get_user_by_name(name)

        try:
            return await web3_client.get_balance(user.address, token_address)
        except Exception as e:
            raise BlockchainError(f"Failed to get balance: {str(e)}")

    async def transfer_from_to(
        self, from_name: str, to_name: str, amount: int, token_address: str
    ) -> str:
        from_user = await self.get_user_by_name(from_name)
        to_user = await self.get_user_by_name(to_name)

        try:
            balance = await web3_client.get_balance(
                from_user.address, token_address
            )
            if balance < amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Available: {balance}, "
                    f"Required: {amount}"
                )
        except InsufficientBalanceError:
            raise
        except Exception as e:
            logger.error("Failed to check balance", error=str(e))
            raise BlockchainError(f"Failed to check balance: {str(e)}")
        return await web3_client.transfer_erc20(
            from_private_key=from_user.private_key,
            to_address=to_user.address,
            amount=amount,
            token_address=token_address,
        )

    async def get_initial_fund(
        self, name: str, user: User | None = None
    ) -> str:
        if user is None:
            user = await self.get_user_by_name(name)

        amount_wei = web3_client.w3.to_wei(
            settings.initial_faucet_gwei, "gwei"
        )

        try:
            return await web3_client.send_native_token(
                from_private_key=settings.faucet_private_key,
                to_address=user.address,
                amount_wei=amount_wei,
            )
        except Exception as e:
            logger.error("Faucet funding failed", name=name, error=str(e))
            raise BlockchainError(f"Faucet funding failed: {str(e)}")
