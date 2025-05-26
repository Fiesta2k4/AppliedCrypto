import requests
import json
from typing import Optional, Dict, Any
from .crypto_service import CryptoService  # ✅ Fixed import

class ApiService:
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        self.crypto = CryptoService()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PersonalVault/1.0'
        })
        
        # Store user credentials for encryption
        self.master_password = None
        self.client_salt = None
    
    def set_tokens(self, access_token: str, refresh_token: str = ""):
        """Set authentication tokens"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        if access_token:
            self.session.headers['Authorization'] = f'Bearer {access_token}'
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     retry: bool = True) -> Optional[Dict]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle different response codes
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            elif response.status_code == 401 and retry and self.refresh_token:
                # Try to refresh token
                if self.refresh_access_token():
                    return self._make_request(method, endpoint, data, retry=False)
            
            # Return error response
            try:
                return response.json()
            except:
                return {"error": f"HTTP {response.status_code}: {response.reason}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to server. Make sure backend is running."}
        except requests.exceptions.Timeout:
            return {"error": "Request timeout. Server may be busy."}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def health_check(self) -> Optional[Dict]:
        """Check API health"""
        return self._make_request('GET', '/health', retry=False)
    
    def register(self, email: str, password: str, public_key: str = "") -> Optional[Dict]:
        """Register new user - SIMPLIFIED VERSION"""
        data = {
            'email': email,
            'password': password,  # ✅ Send plain password, let backend hash it
            'public_key': public_key or "dummy_public_key_for_testing"
        }
        
        response_data = self._make_request('POST', '/auth/register', data, retry=False)
        
        if response_data and 'access_token' in response_data:
            # Auto-login after successful registration
            self.set_tokens(
                response_data['access_token'], 
                response_data.get('refresh_token', '')
            )
            self.user_data = response_data.get('user', {})
            # Store credentials for encryption
            self.master_password = password
            self.client_salt = email  # Use email as salt for simplicity
        
        return response_data
    
    def login(self, email: str, password: str) -> Optional[Dict]:
        """Login - SIMPLIFIED VERSION"""
        try:
            data = {
                'email': email,
                'password': password  # ✅ Send plain password, let backend handle hashing
            }
            
            response_data = self._make_request('POST', '/auth/login', data, retry=False)
            
            if response_data and 'access_token' in response_data:
                # Store tokens and credentials
                self.set_tokens(
                    response_data['access_token'], 
                    response_data.get('refresh_token', '')
                )
                
                self.user_data = response_data.get('user', {})
                # Store credentials for client-side encryption
                self.master_password = password
                self.client_salt = email  # Use email as consistent salt
                
            return response_data
            
        except Exception as e:
            return {"error": f"Login failed: {str(e)}"}
    
    def refresh_access_token(self) -> bool:
        """Refresh access token"""
        if not self.refresh_token:
            return False
        
        # Temporarily set refresh token in header
        old_auth = self.session.headers.get('Authorization')
        self.session.headers['Authorization'] = f'Bearer {self.refresh_token}'
        
        try:
            response_data = self._make_request('POST', '/auth/refresh', retry=False)
            if response_data and 'access_token' in response_data:
                self.set_tokens(response_data['access_token'], self.refresh_token)
                return True
        finally:
            # Restore old auth header
            if old_auth:
                self.session.headers['Authorization'] = old_auth
            else:
                self.session.headers.pop('Authorization', None)
        
        return False
    
    def get_profile(self) -> Optional[Dict]:
        """Get user profile"""
        return self._make_request('GET', '/auth/profile')
    
    def get_vault_entries(self) -> Optional[Dict]:
        """Get all vault entries"""
        return self._make_request('GET', '/vault/')
    
    def create_vault_entry(self, plaintext_data: dict) -> Optional[Dict]:
        """Create encrypted vault entry"""
        try:
            if not self.master_password or not self.client_salt:
                return {"error": "Not authenticated or missing encryption keys"}
            
            # Convert data to JSON string
            plaintext_json = json.dumps(plaintext_data)
            
            # Encrypt data
            encrypted = self.crypto.encrypt_data(
                plaintext_json, 
                self.master_password, 
                self.client_salt
            )
            
            # Add metadata
            metadata = {
                'type': plaintext_data.get('type', 'password'),
                'name': plaintext_data.get('name', 'Unnamed'),
                'created_by': 'client'
            }
            
            # Prepare request
            request_data = {
                'iv': encrypted['iv'],
                'ciphertext': encrypted['ciphertext'],
                'tag': encrypted['tag'],
                'metadata': metadata
            }
            
            return self._make_request('POST', '/vault/', request_data)
            
        except Exception as e:
            return {"error": f"Vault entry creation failed: {str(e)}"}
    
    def get_vault_entries_decrypted(self) -> Optional[Dict]:
        """Get and decrypt vault entries"""
        try:
            # Get encrypted entries
            response = self.get_vault_entries()
            
            if not response or 'entries' not in response:
                return response
            
            # Decrypt each entry
            decrypted_entries = []
            
            for entry in response['entries']:
                try:
                    # Decrypt the entry
                    encrypted_data = {
                        'iv': entry['iv'],
                        'ciphertext': entry['ciphertext'],
                        'tag': entry['tag']
                    }
                    
                    decrypted_json = self.crypto.decrypt_data(
                        encrypted_data,
                        self.master_password,
                        self.client_salt
                    )
                    
                    # Parse decrypted data
                    decrypted_data = json.loads(decrypted_json)
                    
                    # Combine with metadata
                    decrypted_entry = {
                        'id': entry['id'],
                        'metadata': entry['metadata'],
                        'decrypted_data': decrypted_data,
                        'created_at': entry['created_at']
                    }
                    
                    decrypted_entries.append(decrypted_entry)
                    
                except Exception as decrypt_error:
                    # Skip entries that can't be decrypted
                    print(f"Failed to decrypt entry {entry.get('id', 'unknown')}: {decrypt_error}")
                    continue
            
            return {
                'entries': decrypted_entries,
                'count': len(decrypted_entries)
            }
            
        except Exception as e:
            return {"error": f"Failed to get decrypted entries: {str(e)}"}
    
    def get_vault_stats(self) -> Optional[Dict]:
        """Get vault statistics"""
        return self._make_request('GET', '/vault/stats')
    
    def update_vault_entry(self, entry_id: str, **kwargs) -> Optional[Dict]:
        """Update vault entry"""
        return self._make_request('PUT', f'/vault/{entry_id}', kwargs)
    
    def delete_vault_entry(self, entry_id: str) -> Optional[Dict]:
        """Delete vault entry"""
        return self._make_request('DELETE', f'/vault/{entry_id}')
    
    def logout(self):
        """Logout user"""
        self.access_token = None
        self.refresh_token = None
        self.session.headers.pop('Authorization', None)
        self.master_password = None
        self.client_salt = None