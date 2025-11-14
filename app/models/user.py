"""User database model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    """SQLAlchemy model representing an application user."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(
        String, primary_key=True, index=True, nullable=False
    )
    address: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    private_key: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self) -> str:
        return f"<User(name={self.name}, address={self.address})>"
