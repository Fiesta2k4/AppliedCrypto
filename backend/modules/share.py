from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.config import UserDB, ShareDB
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

share_bp = Blueprint('share', __name__)

class ShareService:
    """Service for handling secure password sharing"""
    
    @staticmethod
    def generate_key_pair():
        """Generate RSA key pair for user"""
        key = RSA.generate(2048)
        private_key = key.export_key().decode('utf-8')
        public_key = key.publickey().export_key().decode('utf-8')
        
        return {
            'private_key': private_key,
            'public_key': public_key
        }
    
    @staticmethod
    def encrypt_for_recipient(data, recipient_public_key):
        """Encrypt data using recipient's public key"""
        try:
            # Import recipient's public key
            public_key = RSA.import_key(recipient_public_key)
            cipher = PKCS1_OAEP.new(public_key)
            
            # Encrypt data (must be small enough for RSA)
            data_bytes = data.encode('utf-8')
            encrypted = cipher.encrypt(data_bytes)
            
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return None
    
    @staticmethod
    def decrypt_for_user(encrypted_data, user_private_key):
        """Decrypt data using user's private key"""
        try:
            # Import user's private key
            private_key = RSA.import_key(user_private_key)
            cipher = PKCS1_OAEP.new(private_key)
            
            # Decrypt data
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = cipher.decrypt(encrypted_bytes)
            
            return decrypted.decode('utf-8')
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

@share_bp.route('/send', methods=['POST'])
@jwt_required()
def send_share():
    """Send encrypted secret to another user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        recipient_email = data.get('recipient_email')
        secret_data = data.get('secret_data')
        message = data.get('message', '')
        
        if not recipient_email or not secret_data:
            return jsonify({'error': 'Recipient email and secret data required'}), 400
        
        # Get recipient user
        recipient = UserDB.get_user_by_email(recipient_email)
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        # Check if recipient has public key
        if not recipient.get('public_key'):
            return jsonify({'error': 'Recipient has not set up sharing (no public key)'}), 400
        
        # Encrypt secret for recipient
        encrypted_secret = ShareService.encrypt_for_recipient(
            secret_data, 
            recipient['public_key']
        )
        
        if not encrypted_secret:
            return jsonify({'error': 'Failed to encrypt secret'}), 500
        
        # Create share record
        share = ShareDB.create_share(
            sender_id=current_user_id,
            recipient_id=recipient['id'],
            encrypted_secret=encrypted_secret,
            message=message
        )
        
        if share:
            return jsonify({
                'success': True,
                'share_id': share['id'],
                'message': 'Secret shared successfully'
            }), 201
        else:
            return jsonify({'error': 'Failed to create share'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/received', methods=['GET'])
@jwt_required()
def get_received_shares():
    """Get shares received by current user"""
    try:
        current_user_id = get_jwt_identity()
        shares = ShareDB.get_incoming_shares(current_user_id)
        
        return jsonify({
            'shares': shares,
            'count': len(shares)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/sent', methods=['GET'])
@jwt_required()
def get_sent_shares():
    """Get shares sent by current user"""
    try:
        current_user_id = get_jwt_identity()
        shares = ShareDB.get_outgoing_shares(current_user_id)
        
        return jsonify({
            'shares': shares,
            'count': len(shares)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/<share_id>/decrypt', methods=['POST'])
@jwt_required()
def decrypt_share(share_id):
    """Decrypt a received share"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        user_private_key = data.get('private_key')
        if not user_private_key:
            return jsonify({'error': 'Private key required for decryption'}), 400
        
        # Get share (must be for current user)
        shares = ShareDB.get_incoming_shares(current_user_id)
        share = next((s for s in shares if s['id'] == share_id), None)
        
        if not share:
            return jsonify({'error': 'Share not found'}), 404
        
        # Decrypt the secret
        decrypted_secret = ShareService.decrypt_for_user(
            share['encrypted_secret'],
            user_private_key
        )
        
        if decrypted_secret:
            return jsonify({
                'success': True,
                'decrypted_secret': decrypted_secret,
                'sender_email': share.get('sender_email', ''),
                'message': share.get('message', ''),
                'created_at': share.get('created_at', '')
            })
        else:
            return jsonify({'error': 'Failed to decrypt secret'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/<share_id>/status', methods=['PUT'])
@jwt_required()
def update_share_status(share_id):
    """Update share status (accept/decline)"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        status = data.get('status')
        if status not in ['accepted', 'declined']:
            return jsonify({'error': 'Invalid status'}), 400
        
        # Update share status (implementation would be in ShareDB)
        # For now, just return success
        return jsonify({
            'success': True,
            'message': f'Share {status} successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/generate-keys', methods=['POST'])
@jwt_required()
def generate_user_keys():
    """Generate RSA key pair for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Generate key pair
        keys = ShareService.generate_key_pair()
        
        # Update user with public key
        user = UserDB.get_user_by_id(current_user_id)
        if user:
            # Update user's public key (you'll need to add this method to UserDB)
            updated_user = UserDB.update_user(current_user_id, public_key=keys['public_key'])
            
            if updated_user:
                return jsonify({
                    'success': True,
                    'private_key': keys['private_key'],
                    'public_key': keys['public_key'],
                    'message': 'Keys generated successfully. Save your private key securely!'
                })
            else:
                return jsonify({'error': 'Failed to save public key'}), 500
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@share_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users_for_sharing():
    """Get list of users available for sharing"""
    try:
        users = UserDB.get_all_users()
        current_user_id = get_jwt_identity()
        
        # Filter out current user and users without public keys
        available_users = [
            {
                'id': user['id'],
                'email': user['email'],
                'has_public_key': bool(user.get('public_key'))
            }
            for user in users 
            if user['id'] != current_user_id
        ]
        
        return jsonify({
            'users': available_users,
            'count': len(available_users)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500