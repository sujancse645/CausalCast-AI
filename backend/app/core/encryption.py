import logging
import os

from cryptography.fernet import Fernet

logger = logging.getLogger("encryption")


class EncryptionService:
    def __init__(self) -> None:
        # In a real enterprise system, keys would be fetched from AWS KMS, HashiCorp Vault, etc.
        # This uses an environment variable for the primary key.
        self._primary_key = os.environ.get("ENCRYPTION_PRIMARY_KEY")
        self._fernet: Fernet | None = None
        if self._primary_key:
            try:
                # Ensure it's a valid Fernet key
                self._fernet = Fernet(self._primary_key.encode())
            except Exception:
                logger.exception("Failed to initialize encryption service")

    def encrypt_data(self, plaintext: str) -> str:
        if not self._fernet:
            logger.warning("Encryption key not configured. Returning plaintext (NOT FOR PRODUCTION).")
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt_data(self, ciphertext: str) -> str:
        if not self._fernet:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error("Failed to decrypt data")
            raise ValueError("Decryption failed") from e

    def mask_sensitive_data(self, data: str, show_last: int = 4) -> str:
        """Masks sensitive data, showing only the last N characters."""
        if not data:
            return ""
        if len(data) <= show_last:
            return "*" * len(data)
        return "*" * (len(data) - show_last) + data[-show_last:]


encryption_service = EncryptionService()
