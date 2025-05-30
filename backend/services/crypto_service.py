import hashlib
import secrets
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import argon2

class BackendCryptoService:
    """Server-side cryptographic operations"""
    
    def __init__(self):
        self.argon2_hasher = argon2.PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            salt_len=16
        )
    
    def generate_salt(self):
        """Generate cryptographically secure random salt"""
        return secrets.token_hex(32)  # 256-bit salt
    
    def derive_master_key(self, password, user_salt):
        """Derive master key for vault encryption"""
        # Use PBKDF2 with high iteration count
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            user_salt.encode('utf-8'),
            200000  # Higher iterations for better security
        )
    
    def encrypt_vault_data(self, data, master_key):
        """Encrypt vault data with AES-256-GCM"""
        iv = get_random_bytes(12)  # 96-bit IV for GCM
        cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        
        return {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8')
        }
    
    def decrypt_vault_data(self, iv, ciphertext, tag, master_key):
        """Decrypt vault data"""
        try:
            iv_bytes = base64.b64decode(iv)
            ciphertext_bytes = base64.b64decode(ciphertext)
            tag_bytes = base64.b64decode(tag)
            
            cipher = AES.new(master_key, AES.MODE_GCM, nonce=iv_bytes)
            plaintext = cipher.decrypt_and_verify(ciphertext_bytes, tag_bytes)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

# Global instance
crypto_service = BackendCryptoService()