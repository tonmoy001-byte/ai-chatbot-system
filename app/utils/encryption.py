from cryptography.fernet import Fernet
from typing import Dict, Any
import os

from app.config import get_settings

settings = get_settings()


class DataEncryption:
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY
        self.cipher = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a string."""
        return self.cipher.decrypt(encrypted.encode()).decode()
    
    def encrypt_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PII fields in data."""
        pii_fields = ["email", "phone", "address", "name"]
        encrypted = data.copy()
        for field in pii_fields:
            if field in encrypted and encrypted[field]:
                encrypted[field] = self.encrypt(str(encrypted[field]))
        return encrypted
    
    def decrypt_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields in data."""
        pii_fields = ["email", "phone", "address", "name"]
        decrypted = data.copy()
        for field in pii_fields:
            if field in decrypted and decrypted[field]:
                decrypted[field] = self.decrypt(decrypted[field])
        return decrypted
