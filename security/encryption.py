"""AES encryption for secure token storage."""

import os
import base64
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from utils.logger import get_logger
from config.defaults import ENCRYPTION_KEY_FILE

logger = get_logger(__name__)


class EncryptionManager:
    """Manages encryption for sensitive data."""
    
    def __init__(self, key_file: Path = ENCRYPTION_KEY_FILE):
        self.key_file = key_file
        self._key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        if self._key is not None:
            return self._key
        
        # Try to load existing key
        if self.key_file.exists():
            try:
                with open(self.key_file, "rb") as f:
                    self._key = f.read()
                self._fernet = Fernet(self._key)
                logger.debug("Loaded encryption key from file")
                return self._key
            except Exception as e:
                logger.error(f"Error loading encryption key: {e}")
        
        # Generate new key
        self._key = Fernet.generate_key()
        self._fernet = Fernet(self._key)
        
        # Save key
        try:
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions (Unix)
            if os.name != 'nt':
                os.chmod(self.key_file, 0o600)
            with open(self.key_file, "wb") as f:
                f.write(self._key)
            logger.info("Generated and saved new encryption key")
        except Exception as e:
            logger.error(f"Error saving encryption key: {e}")
        
        return self._key
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        if not data:
            return ""
        
        key = self._get_or_create_key()
        if self._fernet is None:
            self._fernet = Fernet(key)
        
        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string."""
        if not encrypted_data:
            return ""
        
        key = self._get_or_create_key()
        if self._fernet is None:
            self._fernet = Fernet(key)
        
        try:
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager

