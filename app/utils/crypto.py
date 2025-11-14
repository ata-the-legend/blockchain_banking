from cryptography.fernet import Fernet, InvalidToken

from app.settings import settings


class PrivateKeyEncryptionError(RuntimeError):
    """Raised when private key encryption or decryption fails."""


fernet = Fernet(settings.private_key_encryption_key)


def encrypt_private_key(plain_key: str) -> str:
    return fernet.encrypt(plain_key.encode("utf-8")).decode("utf-8")


def decrypt_private_key(token: str) -> str:
    """Decrypt a previously encrypted private key token."""
    print(settings.private_key_encryption_key)

    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise PrivateKeyEncryptionError(
            "Invalid encryption token for private key"
        ) from exc
