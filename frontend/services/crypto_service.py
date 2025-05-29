import hashlib
import secrets
import base64
import json
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes
import argon2

class CryptoService:
    """Client-side cryptographic operations"""
    
    def __init__(self):
        self.argon2_hasher = argon2.PasswordHasher(
            time_cost=3,      # iterations
            memory_cost=65536, # memory in KB
            parallelism=1,    # threads
            hash_len=32,      # output length
            salt_len=16       # salt length
        )
        self.master_key = None
        self.rsa_keypair = None
    
    def generate_salt(self) -> str:
        """Generate random salt"""
        return secrets.token_hex(16)
    
    def derive_key_from_password(self, password: str, salt: str) -> str:
        """Derive key from password using Argon2 (for authentication)"""
        try:
            # Use Argon2 to derive a hash
            hash_result = self.argon2_hasher.hash(password + salt)
            return hash_result
        except Exception as e:
            raise Exception(f"Key derivation failed: {e}")
    
    def derive_master_key(self, password: str, salt: str) -> bytes:
        """Derive master key for vault encryption/decryption"""
        try:
            # Use PBKDF2 to derive 32-byte key for AES-256
            key = hashlib.pbkdf2_hmac('sha256', 
                                     password.encode('utf-8'),
                                     salt.encode('utf-8'),
                                     100000)  # 100k iterations
            return key
        except Exception as e:
            raise Exception(f"Master key derivation failed: {e}")
    
    def derive_encryption_key(self, password: str, salt: str) -> bytes:
        """Derive 32-byte encryption key for AES (alias for derive_master_key)"""
        return self.derive_master_key(password, salt)
    
    def generate_rsa_keypair(self) -> tuple:
        """Generate RSA keypair for sharing"""
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()
        
        self.rsa_keypair = {
            'private': private_key,
            'public': public_key
        }
        
        return private_key, public_key
    
    def encrypt_data(self, data: str, key: bytes) -> dict:
        """Encrypt data using AES-256-GCM with provided key"""
        try:
            # Generate IV
            iv = get_random_bytes(12)  # 96-bit IV for GCM
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            
            # Encrypt data
            ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
            
            return {
                'iv': base64.b64encode(iv).decode('utf-8'),
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'tag': base64.b64encode(tag).decode('utf-8')
            }
            
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")
    
    def encrypt_data_with_password(self, plaintext: str, password: str, salt: str) -> dict:
        """Encrypt data using password-derived key"""
        try:
            # Derive encryption key
            key = self.derive_master_key(password, salt)
            
            # Encrypt with derived key
            return self.encrypt_data(plaintext, key)
            
        except Exception as e:
            raise Exception(f"Password encryption failed: {e}")
    
    def decrypt_data(self, iv: str, ciphertext: str, tag: str, key: bytes) -> str:
        """Decrypt data using AES-256-GCM with provided key"""
        try:
            # Decode base64 components
            iv_bytes = base64.b64decode(iv)
            ciphertext_bytes = base64.b64decode(ciphertext)
            tag_bytes = base64.b64decode(tag)
            
            # Create cipher
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
            
            # Decrypt and verify
            plaintext = cipher.decrypt_and_verify(ciphertext_bytes, tag_bytes)
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")
    
    def decrypt_data_with_password(self, encrypted_data: dict, password: str, salt: str) -> str:
        """Decrypt data using password-derived key"""
        try:
            # Derive encryption key
            key = self.derive_master_key(password, salt)
            
            # Decrypt with derived key
            return self.decrypt_data(
                encrypted_data['iv'],
                encrypted_data['ciphertext'],
                encrypted_data['tag'],
                key
            )
            
        except Exception as e:
            raise Exception(f"Password decryption failed: {e}")
    
    def rsa_encrypt(self, data: str, public_key_pem: str) -> str:
        """Encrypt data with RSA public key"""
        try:
            # Load public key
            public_key = RSA.import_key(public_key_pem)
            cipher = PKCS1_OAEP.new(public_key)
            
            # Encrypt
            encrypted = cipher.encrypt(data.encode('utf-8'))
            
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            raise Exception(f"RSA encryption failed: {e}")
    
    def rsa_decrypt(self, encrypted_data: str, private_key_pem: str) -> str:
        """Decrypt data with RSA private key"""
        try:
            # Load private key
            private_key = RSA.import_key(private_key_pem)
            cipher = PKCS1_OAEP.new(private_key)
            
            # Decrypt
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = cipher.decrypt(encrypted_bytes)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            raise Exception(f"RSA decryption failed: {e}")