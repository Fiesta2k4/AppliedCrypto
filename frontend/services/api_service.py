import requests
import json
from .crypto_service import CryptoService

class ApiService:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.access_token = None
        self.crypto_service = CryptoService()
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # User credentials for encryption
        self.user_password = None
        self.user_salt = None
    
    def set_tokens(self, access_token):
        """Set authentication token"""
        self.access_token = access_token
        if access_token:
            self.session.headers['Authorization'] = f'Bearer {access_token}'
    
    def _make_request(self, method, endpoint, data=None):
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, timeout=10)
            elif method == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                try:
                    return response.json()
                except:
                    return {"error": f"HTTP {response.status_code}"}
                    
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to server"}
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self):
        """Check server health"""
        return self._make_request('GET', '/health')
    
    # Auth methods
    def register(self, email, password):
        """Register new user"""
        data = {'email': email, 'password': password}
        response = self._make_request('POST', '/auth/register', data)
        
        if response and 'access_token' in response:
            self.set_tokens(response['access_token'])
            self.user_password = password
            self.user_salt = email
        
        return response
    
    def login(self, email, password):
        """Login user"""
        data = {'email': email, 'password': password}
        response = self._make_request('POST', '/auth/login', data)
        
        if response and 'access_token' in response:
            self.set_tokens(response['access_token'])
            self.user_password = password
            self.user_salt = email
        
        return response
    
    def get_profile(self):
        """Get user profile"""
        return self._make_request('GET', '/auth/profile')
    
    def get_users(self):
        """Get all users (admin)"""
        return self._make_request('GET', '/auth/users')
    
    # Vault methods
    def create_vault_entry(self, data):
        """Create encrypted vault entry"""
        try:
            if not self.user_password or not self.user_salt:
                return {"error": "Not authenticated"}
            
            # Encrypt data
            plaintext = json.dumps(data)
            master_key = self.crypto_service.derive_master_key(self.user_password, self.user_salt)
            encrypted = self.crypto_service.encrypt_data(plaintext, master_key)
            
            # Add metadata
            metadata = {
                'type': data.get('type', 'password'),
                'name': data.get('name', 'Unnamed')
            }
            
            payload = {
                'iv': encrypted['iv'],
                'ciphertext': encrypted['ciphertext'],
                'tag': encrypted['tag'],
                'metadata': metadata
            }
            
            return self._make_request('POST', '/vault/', payload)
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_vault_entries_decrypted(self):
        """Get and decrypt vault entries"""
        try:
            response = self._make_request('GET', '/vault/')
            
            if not response or 'entries' not in response:
                return {'entries': [], 'count': 0}
            
            if not self.user_password or not self.user_salt:
                return {'entries': [], 'count': 0}
            
            # Decrypt entries
            master_key = self.crypto_service.derive_master_key(self.user_password, self.user_salt)
            decrypted_entries = []
            
            for entry in response['entries']:
                try:
                    decrypted_data = self.crypto_service.decrypt_data(
                        entry['iv'], entry['ciphertext'], entry['tag'], master_key
                    )
                    
                    password_data = json.loads(decrypted_data)
                    
                    decrypted_entries.append({
                        'id': entry['id'],
                        'metadata': entry['metadata'],
                        'decrypted_data': password_data,
                        'created_at': entry['created_at']
                    })
                    
                except Exception as e:
                    print(f"Failed to decrypt entry {entry.get('id')}: {e}")
            
            return {
                'entries': decrypted_entries,
                'count': len(decrypted_entries)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_vault_entries(self):
        """Get raw vault entries for backup"""
        return self._make_request('GET', '/vault/')
    
    def delete_vault_entry(self, entry_id):
        """Delete vault entry"""
        return self._make_request('DELETE', f'/vault/{entry_id}')
    
    def get_vault_stats(self):
        """Get vault statistics"""
        return self._make_request('GET', '/vault/stats')
    
    # OTP methods
    def get_otp_accounts(self):
        """Get OTP accounts"""
        print("🔍 Getting OTP accounts...")
        return self._make_request('GET', '/otp/accounts')

    def add_otp_account(self, issuer, account, secret, digits=6, period=30, algorithm='SHA1'):
        """Add OTP account"""
        data = {
            'issuer': issuer,
            'account': account,
            'secret': secret,
            'digits': digits,
            'period': period,
            'algorithm': algorithm
        }
        print(f"🔍 Adding OTP account: {issuer} - {account}")
        return self._make_request('POST', '/otp/accounts', data)

    def parse_qr_code(self, otpauth_url):
        """Parse QR code"""
        data = {'otpauth_url': otpauth_url}
        print(f"🔍 Parsing QR code...")
        return self._make_request('POST', '/otp/qr-parse', data)

    def generate_all_otps(self):
        """Generate all OTPs"""
        print("🔍 Generating all OTP codes...")
        return self._make_request('GET', '/otp/generate')

    def delete_otp_account(self, account_id):
        """Delete OTP account"""
        print(f"🔍 Deleting OTP account: {account_id}")
        return self._make_request('DELETE', f'/otp/accounts/{account_id}')
    
    # Backup methods
    def create_backup(self, backup_data, name=None):
        """Create backup"""
        
        # ✅ FIX: Ensure name is always provided
        if not name or name.strip() == "":
            from datetime import datetime
            name = f"Backup {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        data = {
            'backup_data': backup_data,
            'name': name.strip()  # Ensure no leading/trailing spaces
        }
        
        print(f"🔍 Creating backup with name: '{name}'")
        print(f"🔍 Backup data keys: {list(backup_data.keys()) if isinstance(backup_data, dict) else 'not dict'}")
        
        return self._make_request('POST', '/backup/create', data)
    
    def get_backups(self):
        """List all backups"""
        return self._make_request('GET', '/backup/list')
    
    def get_backup(self, backup_id):
        """Get specific backup details"""
        return self._make_request('GET', f'/backup/{backup_id}')
    
    def restore_backup(self, backup_id, merge_strategy='merge'):
        """Restore backup data"""
        data = {
            'backup_id': backup_id,
            'merge_strategy': merge_strategy
        }
        response = self._make_request('POST', '/backup/restore', data)
        
        # Process restore response
        if response and 'backup_data' in response:
            backup_data = response['backup_data']
            entries = backup_data.get('encrypted_entries', [])
            
            imported_count = 0
            failed_count = 0
            
            # Import each entry
            for entry in entries:
                try:
                    # Create vault entry from backup
                    result = self._make_request('POST', '/vault/', {
                        'iv': entry['iv'],
                        'ciphertext': entry['ciphertext'], 
                        'tag': entry['tag'],
                        'metadata': entry['metadata']
                    })
                    
                    if result and 'id' in result:
                        imported_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to import entry: {e}")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'failed_count': failed_count,
                'total_count': len(entries),
                'backup_info': {
                    'version': backup_data.get('version', '1.0'),
                    'created_at': backup_data.get('created_at', '')
                }
            }
        
        return response
    
    def delete_backup(self, backup_id):
        """Delete a specific backup"""
        return self._make_request('DELETE', f'/backup/{backup_id}')
    
    def logout(self):
        """Logout user"""
        self.access_token = None
        self.session.headers.pop('Authorization', None)
        self.user_password = None
        self.user_salt = None

    # Share methods
    def generate_user_keys(self):
        """Generate RSA key pair for sharing"""
        return self._make_request('POST', '/share/generate-keys')
    
    def send_share(self, recipient_email, secret_data, message=""):
        """Send encrypted secret to another user"""
        data = {
            'recipient_email': recipient_email,
            'secret_data': secret_data,
            'message': message
        }
        return self._make_request('POST', '/share/send', data)
    
    def get_received_shares(self):
        """Get shares received by current user"""
        return self._make_request('GET', '/share/received')
    
    def get_sent_shares(self):
        """Get shares sent by current user"""
        return self._make_request('GET', '/share/sent')
    
    def decrypt_share(self, share_id, private_key):
        """Decrypt a received share"""
        data = {'private_key': private_key}
        return self._make_request('POST', f'/share/{share_id}/decrypt', data)
    
    def update_share_status(self, share_id, status):
        """Update share status (accept/decline)"""
        data = {'status': status}
        return self._make_request('PUT', f'/share/{share_id}/status', data)
    
    def get_users_for_sharing(self):
        """Get users available for sharing"""
        return self._make_request('GET', '/share/users')