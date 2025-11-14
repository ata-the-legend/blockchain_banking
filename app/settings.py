"""Application settings and configuration management."""

from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str

    # Blockchain Configuration
    rpc_url: str
    token_address: str = "0x7a816c115b8aed1fee7029dd490613f20063b9c3"

    # Faucet Configuration
    faucet_private_key: str

    # API Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Chain Configuration
    chain_id: int = 1000
    gas_limit: int = 100000
    gas_price_gwei: Decimal = Decimal("0.1")
    initial_faucet_gwei: Decimal = Decimal("10")

    # ERC20 ABI
    erc20_abi: list = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "success", "type": "bool"}],
            "type": "function",
        },
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings: Settings = Settings()  # type: ignore[call-arg]
