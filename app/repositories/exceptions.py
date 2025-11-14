"""Custom exceptions for the application."""


class AccountAlreadyExistsError(Exception):
    """Raised when trying to create an account that already exists."""

    pass


class AccountNotFoundError(Exception):
    """Raised when an account is not found in the database."""

    pass


class InsufficientBalanceError(Exception):
    """Raised when an account has insufficient balance for a transaction."""

    pass


class BlockchainError(Exception):
    """Raised when a blockchain operation fails."""

    pass


class InvalidAddressError(Exception):
    """Raised when an Ethereum address is invalid."""

    pass
