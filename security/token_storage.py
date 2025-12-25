"""Secure token storage."""

import json
from pathlib import Path
from typing import Optional, Dict, Any

from utils.logger import get_logger
from .encryption import get_encryption_manager
from config.defaults import TOKEN_STORAGE_FILE

logger = get_logger(__name__)


class TokenStorage:
    """Secure storage for platform tokens."""
    
    def __init__(self, storage_file: Path = TOKEN_STORAGE_FILE):
        self.storage_file = storage_file
        self.encryption = get_encryption_manager()
        self._tokens: Dict[str, Any] = {}
        self._load()
    
    def _load(self):
        """Load tokens from file."""
        if not self.storage_file.exists():
            logger.debug("Token storage file does not exist, starting empty")
            return
        
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                encrypted_data = f.read()
            
            if encrypted_data:
                decrypted_data = self.encryption.decrypt(encrypted_data)
                self._tokens = json.loads(decrypted_data)
                logger.debug(f"Loaded {len(self._tokens)} tokens from storage")
        except Exception as e:
            logger.error(f"Error loading tokens: {e}")
            self._tokens = {}
    
    def _save(self):
        """Save tokens to file."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            data_json = json.dumps(self._tokens, ensure_ascii=False)
            encrypted_data = self.encryption.encrypt(data_json)
            
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
            
            logger.debug("Tokens saved to storage")
        except Exception as e:
            logger.error(f"Error saving tokens: {e}")
    
    def store_token(self, platform: str, token: str, metadata: Optional[Dict[str, Any]] = None):
        """Store a token for a platform."""
        self._tokens[platform] = {
            "token": token,
            "metadata": metadata or {}
        }
        self._save()
        logger.info(f"Stored token for platform: {platform}")
    
    def get_token(self, platform: str) -> Optional[str]:
        """Get a token for a platform."""
        if platform in self._tokens:
            return self._tokens[platform].get("token")
        return None
    
    def get_metadata(self, platform: str) -> Dict[str, Any]:
        """Get metadata for a platform."""
        if platform in self._tokens:
            return self._tokens[platform].get("metadata", {})
        return {}
    
    def remove_token(self, platform: str):
        """Remove a token for a platform."""
        if platform in self._tokens:
            del self._tokens[platform]
            self._save()
            logger.info(f"Removed token for platform: {platform}")
    
    def list_platforms(self) -> list[str]:
        """List all platforms with stored tokens."""
        return list(self._tokens.keys())

