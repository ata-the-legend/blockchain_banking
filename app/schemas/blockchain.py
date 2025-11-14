"""Blockchain-related Pydantic schemas."""

from pydantic import BaseModel, Field, field_validator


class BlockchainAccount(BaseModel):
    """Schema representing a generated blockchain account."""

    address: str = Field(..., description="Checksummed blockchain address")
    private_key: str = Field(..., description="Private key in hex format")

    @field_validator("address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        """Ensure the address has the correct basic format."""
        if not value.startswith("0x") or len(value) != 42:
            raise ValueError("Invalid blockchain address format")
        return value

    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, value: str) -> str:
        """Ensure the private key looks like a hex string."""
        if not value.startswith("0x"):
            raise ValueError(
                "Private key must be a hex string starting with 0x"
            )
        return value
