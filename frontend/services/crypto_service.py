import hashlib
import secrets
import base64
import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import argon2

class CryptoService:
    """Client-side cryptographic operations"""
    
    def __init__(self):
        self.argon2_hasher = argon2.PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            salt_len=16
        )
    
    def generate_salt(self):
        """Generate random salt"""
        return secrets.token_hex(16)
    
    def derive_master_key(self, password, salt):
        """Derive master key for encryption"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
    
    def encrypt_data(self, data, key):
        """Encrypt data with AES-256-GCM"""
        iv = get_random_bytes(12)
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
        
        return {
            'iv': base64.b64encode(iv).decode('utf-8'),
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8')
        }
    
    def decrypt_data(self, iv, ciphertext, tag, key):
        """Decrypt data with AES-256-GCM"""
        iv_bytes = base64.b64decode(iv)
        ciphertext_bytes = base64.b64decode(ciphertext)
        tag_bytes = base64.b64decode(tag)
        
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
        plaintext = cipher.decrypt_and_verify(ciphertext_bytes, tag_bytes)
        
        return plaintext.decode('utf-8')