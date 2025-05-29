from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import hmac
import hashlib
import base64
import struct
import time
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from urllib.parse import urlparse, parse_qs
from database.config import OTPDB

otp_bp = Blueprint('otp', __name__)

class OTPService:
    """OTP service for TOTP generation"""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
    
    def _get_encryption_key(self):
        """Get OTP encryption key"""
        server_secret = os.getenv('OTP_ENCRYPTION_KEY', 'default-otp-key')
        return hashlib.sha256(server_secret.encode()).digest()
    
    def _encrypt_secret(self, secret):
        """Encrypt OTP secret"""
        iv = get_random_bytes(12)
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(secret.encode('utf-8'))
        return base64.b64encode(iv + ciphertext + tag).decode('utf-8')
    
    def _decrypt_secret(self, encrypted_secret):
        """Decrypt OTP secret"""
        data = base64.b64decode(encrypted_secret)
        iv, ciphertext, tag = data[:12], data[12:-16], data[-16:]
        cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=iv)
        secret = cipher.decrypt_and_verify(ciphertext, tag)
        return secret.decode('utf-8')
    
    def generate_totp(self, secret, digits=6, period=30, algorithm='SHA1'):
        """Generate TOTP code"""
        try:
            # Clean secret
            secret = secret.replace(' ', '').replace('-', '').upper()
            missing_padding = len(secret) % 8
            if missing_padding:
                secret += '=' * (8 - missing_padding)
            
            key = base64.b32decode(secret)
            
            # Calculate counter
            counter = int(time.time()) // period
            counter_bytes = struct.pack('>Q', counter)
            
            # Generate HMAC
            hash_func = getattr(hashlib, algorithm.lower())
            hmac_digest = hmac.new(key, counter_bytes, hash_func).digest()
            
            # Dynamic truncation
            offset = hmac_digest[-1] & 0x0F
            truncated = hmac_digest[offset:offset+4]
            code_int = struct.unpack('>I', truncated)[0] & 0x7FFFFFFF
            
            return str(code_int % (10 ** digits)).zfill(digits)
            
        except Exception as e:
            print(f"TOTP generation error: {e}")
            return None
    
    def parse_otpauth_url(self, url):
        """Parse otpauth:// URL"""
        try:
            if not url.startswith('otpauth://'):
                return {'success': False, 'error': 'Invalid URL format'}
            
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            path_parts = parsed.path.lstrip('/').split(':')
            issuer = params.get('issuer', [''])[0] or (path_parts[0] if len(path_parts) > 1 else '')
            account = path_parts[-1] if path_parts else ''
            secret = params.get('secret', [''])[0]
            
            if not secret:
                return {'success': False, 'error': 'No secret found'}
            
            return {
                'success': True,
                'issuer': issuer,
                'account': account,
                'secret': secret,
                'digits': int(params.get('digits', ['6'])[0]),
                'period': int(params.get('period', ['30'])[0]),
                'algorithm': params.get('algorithm', ['SHA1'])[0]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize service
otp_service = OTPService()

@otp_bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_otp_accounts():
    """Get OTP accounts"""
    try:
        user_id = get_jwt_identity()
        accounts = OTPDB.get_user_otp_secrets(user_id)
        
        return jsonify({
            'success': True,
            'accounts': accounts,
            'count': len(accounts)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@otp_bp.route('/accounts', methods=['POST'])
@jwt_required()
def add_otp_account():
    """Add OTP account"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate
        required = ['issuer', 'account', 'secret']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} required'}), 400
        
        # Encrypt secret
        encrypted_secret = otp_service._encrypt_secret(data['secret'])
        
        # Create account
        account = OTPDB.create_otp_secret(
            user_id=user_id,
            issuer=data['issuer'],
            account=data['account'],
            encrypted_secret=encrypted_secret,
            digits=data.get('digits', 6),
            period=data.get('period', 30),
            algorithm=data.get('algorithm', 'SHA1')
        )
        
        if account:
            return jsonify({
                'success': True,
                'account_id': account['id']
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create account'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@otp_bp.route('/qr-parse', methods=['POST'])
@jwt_required()
def parse_qr_code():
    """Parse QR code URL"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('otpauth_url'):
            return jsonify({'success': False, 'error': 'URL required'}), 400
        
        # Parse URL
        parsed = otp_service.parse_otpauth_url(data['otpauth_url'])
        if not parsed['success']:
            return jsonify(parsed), 400
        
        # Encrypt and create account
        encrypted_secret = otp_service._encrypt_secret(parsed['secret'])
        
        account = OTPDB.create_otp_secret(
            user_id=user_id,
            issuer=parsed['issuer'],
            account=parsed['account'],
            encrypted_secret=encrypted_secret,
            digits=parsed['digits'],
            period=parsed['period'],
            algorithm=parsed['algorithm']
        )
        
        if account:
            return jsonify({
                'success': True,
                'account_id': account['id'],
                'parsed_data': parsed
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create account'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@otp_bp.route('/generate', methods=['GET'])
@jwt_required()
def generate_all_otps():
    """Generate OTP codes for all accounts"""
    try:
        user_id = get_jwt_identity()
        accounts = OTPDB.get_user_otp_secrets(user_id)
        otp_list = []
        
        for account in accounts:
            try:
                # Get encrypted secret
                full_account = OTPDB.get_otp_secret_by_id(account['id'], user_id)
                secret = otp_service._decrypt_secret(full_account['encrypted_secret'])
                
                # Generate OTP
                otp_code = otp_service.generate_totp(
                    secret, 
                    account['digits'], 
                    account['period'], 
                    account['algorithm']
                )
                
                if otp_code:
                    current_time = int(time.time())
                    time_remaining = account['period'] - (current_time % account['period'])
                    
                    otp_list.append({
                        'id': account['id'],
                        'issuer': account['issuer'],
                        'account': account['account'],
                        'otp_code': otp_code,
                        'time_remaining': time_remaining,
                        'period': account['period'],
                        'digits': account['digits']
                    })
                    
            except Exception as e:
                print(f"Error generating OTP for account {account['id']}: {e}")
        
        return jsonify({
            'success': True,
            'otp_accounts': otp_list,
            'count': len(otp_list)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@otp_bp.route('/accounts/<account_id>', methods=['DELETE'])
@jwt_required()
def delete_otp_account(account_id):
    """Delete OTP account"""
    try:
        user_id = get_jwt_identity()
        
        if OTPDB.delete_otp_secret(account_id, user_id):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Account not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500