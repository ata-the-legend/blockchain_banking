"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new user account."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Unique username"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate username contains only alphanumeric and underscores."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Name must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        return v


class UserResponse(BaseModel):
    """Schema for user account response."""

    name: str
    address: str
    private_key: str
    faucet_tx_hash: str | None = None

    model_config = {"from_attributes": True}


class BalanceRequest(BaseModel):
    """Schema for balance query request."""

    name: str = Field(..., min_length=1, description="Username")
    token_address: str = Field(..., description="ERC20 token contract address")

    @field_validator("token_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v


class BalanceResponse(BaseModel):
    """Schema for balance query response."""

    name: str
    address: str
    token_address: str
    balance: int = Field(
        ..., description="Token balance in wei (smallest unit)"
    )


class TransferRequest(BaseModel):
    """Schema for token transfer request."""

    from_name: str = Field(..., min_length=1, description="Sender username")
    to_name: str = Field(..., min_length=1, description="Recipient username")
    amount: int = Field(..., gt=0, description="Amount to transfer in wei")
    token_address: str = Field(..., description="ERC20 token contract address")

    @field_validator("token_address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        return v


class TransferResponse(BaseModel):
    """Schema for token transfer response."""

    success: bool
    tx_hash: str | None = None
    from_address: str
    to_address: str
    amount: int
    message: str | None = None


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    error_code: str | None = None
