"""API routes for blockchain banking operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.account import AccountRepository
from app.repositories.exceptions import (
    AccountAlreadyExistsError,
    AccountNotFoundError,
    InsufficientBalanceError,
    BlockchainError,
)
from app.schemas.user import (
    UserCreate,
    UserResponse,
    BalanceResponse,
    TransferRequest,
    TransferResponse,
)
from app.schemas.blockchain import Tokens, token_address_mapping
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["Blockchain Banking"])


@router.post(
    "/create_account",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_account(
    user_data: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserResponse:

    try:
        repo = AccountRepository(db)
        return await repo.create_account(user_data.name)
    except AccountAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )


@router.get("/get_balance", response_model=BalanceResponse)
async def get_balance(
    name: str, token: Tokens, db: AsyncSession = Depends(get_db)
) -> BalanceResponse:
    try:
        repo = AccountRepository(db)
        user = await repo.get_user_by_name(name)
        token_address = token_address_mapping(token)
        balance = await repo.get_balance(name, token_address)
        return BalanceResponse(
            name=name,
            address=user.address,
            token=token,
            token_address=token_address,
            balance=balance,
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except BlockchainError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to get balance", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}",
        )


@router.post("/transfer", response_model=TransferResponse)
async def transfer(
    transfer_data: TransferRequest, db: AsyncSession = Depends(get_db)
) -> TransferResponse:
    try:
        repo = AccountRepository(db)

        from_user = await repo.get_user_by_name(transfer_data.from_name)
        to_user = await repo.get_user_by_name(transfer_data.to_name)

        tx_hash = await repo.transfer_from_to(
            from_name=transfer_data.from_name,
            to_name=transfer_data.to_name,
            amount=transfer_data.amount,
            token_address=token_address_mapping(transfer_data.token),
        )

        return TransferResponse(
            success=True,
            tx_hash=tx_hash,
            from_address=from_user.address,
            to_address=to_user.address,
            amount=transfer_data.amount,
            token=transfer_data.token,
            message="Transfer successful",
        )
    except AccountNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
