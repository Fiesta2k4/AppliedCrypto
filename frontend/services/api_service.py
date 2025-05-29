import requests
import json
from typing import Optional, Dict, Any
from .crypto_service import CryptoService  # ✅ Fixed import
from datetime import datetime
import uuid

class ApiService:
    def __init__(self, base_url: str = "http://localhost:5000/api"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_data = None
        self.crypto_service = CryptoService()  # ✅ Changed from self.crypto
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PersonalVault/1.0'
        })
        
        # Store user credentials for encryption
        self.user_password = None  # ✅ Changed from master_password
        self.user_salt = None      # ✅ Changed from client_salt
    
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
        """Register new user"""
        data = {
            'email': email,
            'password': password,
            'public_key': public_key or "dummy_public_key_for_testing"
        }
        
        response_data = self._make_request('POST', '/auth/register', data, retry=False)
        
        if response_data and 'access_token' in response_data:
            self.set_tokens(
                response_data['access_token'], 
                response_data.get('refresh_token', '')
            )
            self.user_data = response_data.get('user', {})
            # Store credentials for encryption
            self.user_password = password  # ✅ Updated
            self.user_salt = email         # ✅ Updated
        
        return response_data
    
    def login(self, email: str, password: str) -> Optional[Dict]:
        """Login with detailed debugging"""
        try:
            print(f"🔍 === API SERVICE LOGIN ===")
            print(f"🔍 Login attempt for: {email}")
            print(f"🔍 Base URL: {self.base_url}")
            
            data = {
                'email': email,
                'password': password
            }
            
            print("🔍 Making login request...")
            response_data = self._make_request('POST', '/auth/login', data, retry=False)
            
            print(f"🔍 Login response: {response_data}")
            
            if response_data and 'access_token' in response_data:
                access_token = response_data['access_token']
                refresh_token = response_data.get('refresh_token', '')
                
                print(f"🔍 Setting tokens...")
                print(f"🔍 Access token: {access_token[:50]}..." if access_token else "None")
                
                # Set tokens
                self.set_tokens(access_token, refresh_token)
                
                # Store user data and credentials
                self.user_data = response_data.get('user', {})
                self.user_password = password
                self.user_salt = email
                
                print(f"✅ Login successful!")
                print(f"🔍 Token set: {self.access_token[:50]}..." if self.access_token else "None")
                print(f"🔍 Session auth header: {self.session.headers.get('Authorization', 'NOT SET')}")
                
                # Test API immediately
                print("🔍 Testing API immediately after login...")
                test_result = self._make_request('GET', '/auth/profile')
                print(f"🔍 Profile test result: {test_result}")
                
            else:
                print(f"❌ Login failed - no access token in response")
                
            return response_data
        
        except Exception as e:
            print(f"❌ Login API error: {e}")
            import traceback
            traceback.print_exc()
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
            if not self.user_password or not self.user_salt:
                return {"error": "Not authenticated or missing encryption keys"}
            
            print(f"🔐 Creating vault entry: {plaintext_data.get('name', 'unnamed')}")
            
            # Convert data to JSON string
            plaintext_json = json.dumps(plaintext_data)
            print(f"🔍 Data to encrypt: {plaintext_json}")
            
            # Derive master key
            master_key = self.crypto_service.derive_master_key(
                self.user_password,
                self.user_salt
            )
            
            print(f"🔍 Master key derived: {len(master_key)} bytes")
            
            # Encrypt data with AES-256-GCM
            encrypted = self.crypto_service.encrypt_data(plaintext_json, master_key)
            
            print(f"🔍 Encrypted data: iv={encrypted['iv'][:10]}..., cipher={encrypted['ciphertext'][:20]}...")
            
            # Add metadata (unencrypted)
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
            
            print(f"🔍 Sending to backend: {request_data.keys()}")
            
            response = self._make_request('POST', '/vault/', request_data)
            
            if response and 'id' in response:
                print(f"✅ Vault entry created: {response['id']}")
            else:
                print(f"❌ Create failed: {response}")
        
            return response
        
        except Exception as e:
            print(f"❌ Create vault entry error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Vault entry creation failed: {str(e)}"}
    
    def get_vault_entries_decrypted(self):
        """Get entries and decrypt them client-side"""
        try:
            # Step 1: Get encrypted entries from backend
            encrypted_entries = self._make_request('GET', '/vault/')
            
            print(f"🔍 API Response: {encrypted_entries}")
            
            if not encrypted_entries or 'entries' not in encrypted_entries:
                return {'entries': [], 'count': 0}
            
            # Check authentication
            if not self.user_password or not self.user_salt:
                print("❌ Missing user credentials for decryption")
                return {'entries': [], 'count': 0}
            
            # Step 2: Derive master key
            master_key = self.crypto_service.derive_master_key(
                self.user_password, 
                self.user_salt
            )
            
            print(f"🔍 Master key derived: {len(master_key)} bytes")
            
            # Step 3: Decrypt each entry
            decrypted_entries = []
            for entry in encrypted_entries['entries']:
                try:
                    print(f"🔍 Processing entry: {entry.get('id', 'NO ID')}")
                    
                    # Decrypt password data
                    decrypted_data = self.crypto_service.decrypt_data(
                        iv=entry['iv'],
                        ciphertext=entry['ciphertext'],
                        tag=entry['tag'],
                        key=master_key
                    )
                    
                    print(f"🔍 Decrypted data: {decrypted_data[:50]}...")
                    
                    # Parse JSON
                    password_data = json.loads(decrypted_data)
                    
                    # Add to result WITH ENTRY ID
                    decrypted_entries.append({
                        'id': entry['id'],
                        'iv': entry['iv'],
                        'ciphertext': entry['ciphertext'],
                        'tag': entry['tag'],
                        'metadata': entry['metadata'],
                        'decrypted_data': password_data,
                        'created_at': entry['created_at']
                    })
                    
                    print(f"✅ Decrypted entry: {entry['id']} - {password_data.get('name', 'unnamed')}")
                    
                except Exception as e:
                    print(f"❌ Failed to decrypt entry {entry.get('id', 'unknown')}: {e}")
                    import traceback
                    traceback.print_exc()
        
            print(f"✅ Successfully decrypted {len(decrypted_entries)} entries")
            
            return {
                'entries': decrypted_entries,
                'count': len(decrypted_entries)
            }
            
        except Exception as e:
            print(f"❌ Get vault entries error: {e}")
            import traceback
            traceback.print_exc()
            return {'entries': [], 'count': 0}
    
    def get_vault_stats(self) -> Optional[Dict]:
        """Get vault statistics"""
        return self._make_request('GET', '/vault/stats')
    
    def update_vault_entry(self, entry_id: str, **kwargs) -> Optional[Dict]:
        """Update vault entry"""
        return self._make_request('PUT', f'/vault/{entry_id}', kwargs)
    
    def delete_vault_entry(self, entry_id):
        """Delete vault entry"""
        try:
            response_data = self._make_request('DELETE', f'/vault/{entry_id}')
            return response_data
        
        except Exception as e:
            print(f"Delete entry error: {e}")
            return {'error': str(e)}
    
    def logout(self):
        """Logout user"""
        self.access_token = None
        self.refresh_token = None
        self.session.headers.pop('Authorization', None)
        self.user_password = None  # ✅ Updated
        self.user_salt = None      # ✅ Updated
    
    # Backup methods
    def create_backup(self, backup_data, name=None):
        """Create backup with given data"""
        try:
            if not name:
                name = f"Backup {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            payload = {
                'backup_data': backup_data,
                'name': name
            }
            
            return self._make_request('POST', '/backup/create', payload)
            
        except Exception as e:
            print(f"Create backup error: {e}")
            return {'error': str(e)}

    def get_backups(self):
        """Get list of user's backups with detailed debugging"""
        try:
            print("🔍 === API SERVICE GET_BACKUPS ===")
            print(f"🔍 Base URL: {self.base_url}")
            print(f"🔍 Access token exists: {self.access_token is not None}")
            print(f"🔍 Session headers: {dict(self.session.headers)}")
            
            # Make the request
            print("🔍 Making request to /backup/list...")
            result = self._make_request('GET', '/backup/list')
            
            print(f"🔍 _make_request returned: {result}")
            print(f"🔍 Result type: {type(result)}")
            
            if isinstance(result, dict):
                print(f"🔍 Result keys: {list(result.keys())}")
                
                if 'error' in result:
                    print(f"❌ API returned error: {result['error']}")
                
                if 'backups' in result:
                    backups = result['backups']
                    print(f"🔍 Backups in response: {len(backups)}")
                    for i, backup in enumerate(backups):
                        print(f"🔍 Backup {i}: ID={backup.get('id')}, Name={backup.get('name')}")
            
            return result
            
        except Exception as e:
            print(f"❌ Get backups error: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    def restore_backup(self, backup_id, merge_strategy='merge'):
        """Restore backup and import entries"""
        try:
            # Get backup data from server
            backup_response = self._make_request('POST', '/backup/restore', {
                'backup_id': backup_id,
                'merge_strategy': merge_strategy
            })
            
            if not backup_response or 'backup_data' not in backup_response:
                return {'error': 'Failed to get backup data'}
            
            backup_data = backup_response['backup_data']
            print(f"🔍 Backup data received: {backup_data.get('entry_count', 0)} entries")
            
            # Process the encrypted entries from backup
            return self.import_backup_entries(backup_data, merge_strategy)
            
        except Exception as e:
            print(f"Restore backup error: {e}")
            return {'error': str(e)}

    def import_backup_entries(self, backup_data, merge_strategy='merge'):
        """Import entries from backup data into current vault"""
        try:
            if 'encrypted_entries' not in backup_data:
                return {'error': 'No entries found in backup'}
            
            encrypted_entries = backup_data['encrypted_entries']
            imported_count = 0
            failed_count = 0
            skipped_count = 0
            
            # Get current vault entries to check for duplicates
            current_entries = self.get_vault_entries()
            current_ids = set()
            if current_entries and 'entries' in current_entries:
                current_ids = {entry['id'] for entry in current_entries['entries']}
            
            print(f"🔍 Current vault has {len(current_ids)} entries")
            print(f"🔍 Backup has {len(encrypted_entries)} entries to import")
            
            for entry in encrypted_entries:
                try:
                    entry_id = entry.get('id')
                    entry_name = entry.get('metadata', {}).get('name', 'Unnamed')
                    
                    # Check for duplicates based on merge strategy
                    if entry_id in current_ids:
                        if merge_strategy == 'skip_duplicates':
                            print(f"⏭️ Skipping duplicate: {entry_name} ({entry_id})")
                            skipped_count += 1
                            continue
                        elif merge_strategy == 'merge':
                            print(f"🔄 Updating existing: {entry_name} ({entry_id})")
                            # For merge strategy, we'll create a new entry with different ID
                            entry = dict(entry)  # Make a copy
                            entry['id'] = str(uuid.uuid4())  # Generate new ID
                            entry['metadata']['name'] = f"{entry_name} (Restored)"
                    
                    # Import entry by re-creating it in vault
                    result = self.import_single_entry(entry)
                    
                    if result and 'id' in result:
                        imported_count += 1
                        print(f"✅ Imported: {entry_name}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to import: {entry_name}")
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error importing entry: {e}")
            
            # Return import summary
            return {
                'success': True,
                'imported_count': imported_count,
                'failed_count': failed_count,
                'skipped_count': skipped_count,
                'total_count': len(encrypted_entries),
                'backup_info': {
                    'version': backup_data.get('version'),
                    'backup_type': backup_data.get('backup_type'),
                    'created_at': backup_data.get('created_at')
                }
            }
            
        except Exception as e:
            print(f"Import backup entries error: {e}")
            return {'error': str(e)}

    def import_single_entry(self, encrypted_entry):
        """Import a single encrypted entry into vault"""
        try:
            # Prepare the entry data for vault creation
            payload = {
                'iv': encrypted_entry['iv'],
                'ciphertext': encrypted_entry['ciphertext'],
                'tag': encrypted_entry['tag'],
                'metadata': encrypted_entry['metadata']
            }
            
            # Create entry in vault using existing API endpoint
            return self._make_request('POST', '/vault/', payload)
            
        except Exception as e:
            print(f"Import single entry error: {e}")
            return {'error': str(e)}

    def debug_current_token(self):
        """Debug method to print current access token"""
        print(f"🔍 === API SERVICE DEBUG ===")
        print(f"🔍 Base URL: {self.base_url}")
        print(f"🔍 Access Token: {self.access_token}")
        print(f"🔍 Token length: {len(self.access_token) if self.access_token else 0}")
        print(f"🔍 Session headers: {dict(self.session.headers)}")
        
        if self.access_token:
            # Decode JWT payload (without verification, just for debugging)
            try:
                import base64
                import json
                
                # Split JWT token
                parts = self.access_token.split('.')
                if len(parts) == 3:
                    # Decode payload (middle part)
                    payload = parts[1]
                    # Add padding if needed
                    padding = 4 - len(payload) % 4
                    if padding != 4:
                        payload += '=' * padding
                    
                    decoded = base64.urlsafe_b64decode(payload)
                    payload_data = json.loads(decoded)
                    
                    print(f"🔍 Token payload: {payload_data}")
                    print(f"🔍 User ID: {payload_data.get('sub')}")
                    print(f"🔍 Expires: {payload_data.get('exp')}")
                else:
                    print("❌ Invalid JWT format")
                    
            except Exception as e:
                print(f"❌ Token decode error: {e}")
        
        # Return token for manual use
        return self.access_token
    
    def send_share(self, recipient_email: str, secret_data: str, message: str = "") -> Optional[Dict]:
        """Send encrypted secret to another user"""
        try:
            data = {
                'recipient_email': recipient_email,
                'secret_data': secret_data,
                'message': message
            }
            
            return self._make_request('POST', '/share/send', data)
            
        except Exception as e:
            print(f"Send share error: {e}")
            return {'error': str(e)}

    def get_vault_users(self) -> Optional[Dict]:
        """Get list of registered vault users for sharing"""
        try:
            print("🔍 Getting vault users via auth/users endpoint...")
            return self._make_request('GET', '/auth/users')
            
        except Exception as e:
            print(f"Get vault users error: {e}")
            return {'error': str(e)}

    def send_internal_share(self, recipient_id: str, secret_data: str, message: str = "") -> Optional[Dict]:
        """Send encrypted secret to internal vault user"""
        try:
            data = {
                'recipient_id': recipient_id,
                'secret_data': secret_data,
                'message': message
            }
            
            return self._make_request('POST', '/share/send-internal', data)
            
        except Exception as e:
            print(f"Send internal share error: {e}")
            return {'error': str(e)}

    def get_incoming_shares(self) -> Optional[Dict]:
        """Get shares received by current user"""
        try:
            return self._make_request('GET', '/share/incoming')
            
        except Exception as e:
            print(f"Get incoming shares error: {e}")
            return {'error': str(e)}

    def get_outgoing_shares(self) -> Optional[Dict]:
        """Get shares sent by current user"""
        try:
            return self._make_request('GET', '/share/outgoing')
            
        except Exception as e:
            print(f"Get outgoing shares error: {e}")
            return {'error': str(e)}

    def decrypt_internal_share(self, share_id: str) -> Optional[Dict]:
        """Decrypt and retrieve shared secret from internal user"""
        try:
            data = {'share_id': share_id}
            return self._make_request('POST', '/share/decrypt-internal', data)
            
        except Exception as e:
            print(f"Decrypt internal share error: {e}")
            return {'error': str(e)}