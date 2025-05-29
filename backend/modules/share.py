from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.helpers import UserDB, ShareDB
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import traceback

share_bp = Blueprint('share', __name__)

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
            return jsonify({"error": "Recipient email and secret data are required"}), 400
        
        # Get recipient's info
        recipient = UserDB.get_user_by_email(recipient_email)
        if not recipient:
            return jsonify({"error": "Recipient not found"}), 404
        
        if not recipient.get('public_key'):
            return jsonify({"error": "Recipient has no public key"}), 400
        
        # Encrypt secret with recipient's public key
        try:
            public_key = RSA.import_key(recipient['public_key'])
            cipher_rsa = PKCS1_OAEP.new(public_key)
            encrypted_secret = cipher_rsa.encrypt(secret_data.encode('utf-8'))
            encrypted_secret_b64 = base64.b64encode(encrypted_secret).decode('utf-8')
        except Exception as e:
            return jsonify({"error": f"Encryption failed: {str(e)}"}), 500
        
        # Create share record
        share = ShareDB.create_share(
            sender_id=current_user_id,
            recipient_email=recipient_email,
            encrypted_secret=encrypted_secret_b64,
            message=message
        )
        
        if share:
            return jsonify({
                "message": "Secret shared successfully",
                "share_id": share['id'],
                "recipient": recipient_email
            }), 201
        else:
            return jsonify({"error": "Failed to create share"}), 500
        
    except Exception as e:
        print(f"❌ Share send error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Share failed: {str(e)}"}), 500

@share_bp.route('/decrypt', methods=['POST'])
@jwt_required()
def decrypt_share():
    """Decrypt and retrieve shared secret"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        share_id = data.get('share_id')
        if not share_id:
            return jsonify({"error": "Share ID is required"}), 400
        
        # Get share
        share = ShareDB.get_share_by_id(share_id)
        if not share:
            return jsonify({"error": "Share not found"}), 404
        
        # Verify this user is the recipient
        current_user = UserDB.get_user_by_id(current_user_id)
        if not current_user or share['recipient_email'] != current_user['email']:
            return jsonify({"error": "Access denied"}), 403
        
        # For client-side decryption, return encrypted secret
        # User will decrypt with their private key client-side
        return jsonify({
            "share_id": share_id,
            "encrypted_secret": share['encrypted_secret'],
            "sender_email": share.get('sender_email', 'Unknown'),
            "message": share.get('message', ''),
            "created_at": share.get('created_at', ''),
            "requires_client_decryption": True
        }), 200
        
    except Exception as e:
        print(f"❌ Decrypt share error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

@share_bp.route('/send-internal', methods=['POST'])
@jwt_required()
def send_internal_share():
    """Send encrypted secret to internal vault user"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        recipient_id = data.get('recipient_id')
        secret_data = data.get('secret_data')
        message = data.get('message', '')
        
        if not recipient_id or not secret_data:
            return jsonify({"error": "Recipient ID and secret data are required"}), 400
        
        # Verify recipient exists and is active
        recipient = UserDB.get_user_by_id(recipient_id)
        if not recipient or not recipient.get('is_active'):
            return jsonify({"error": "Recipient not found or inactive"}), 404
        
        # For internal sharing, we can store the secret encrypted with a shared key
        # or use simple encoding since it's within the same vault system
        
        # Simple base64 encoding for internal sharing (you can enhance with proper encryption)
        import base64
        encoded_secret = base64.b64encode(secret_data.encode('utf-8')).decode('utf-8')
        
        # Create share record
        share = ShareDB.create_share(
            sender_id=current_user_id,
            recipient_id=recipient_id,
            encrypted_secret=encoded_secret,
            message=message
        )
        
        if share:
            return jsonify({
                "message": "Secret shared successfully with vault user",
                "share_id": share['id'],
                "recipient_id": recipient_id,
                "recipient_email": recipient['email']
            }), 201
        else:
            return jsonify({"error": "Failed to create internal share"}), 500
        
    except Exception as e:
        print(f"❌ Send internal share error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Internal share failed: {str(e)}"}), 500

@share_bp.route('/decrypt-internal', methods=['POST'])
@jwt_required()
def decrypt_internal_share():
    """Decrypt and retrieve internal shared secret"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        share_id = data.get('share_id')
        if not share_id:
            return jsonify({"error": "Share ID is required"}), 400
        
        # Get share with sender/recipient info
        share = ShareDB.get_share_by_id(share_id)
        if not share:
            return jsonify({"error": "Share not found"}), 404
        
        # Verify this user is the recipient
        if share['recipient_id'] != current_user_id:
            return jsonify({"error": "Access denied - you are not the recipient"}), 403
        
        # Decode the internal secret
        import base64
        try:
            decrypted_secret = base64.b64decode(share['encrypted_secret']).decode('utf-8')
        except Exception as e:
            return jsonify({"error": f"Failed to decode secret: {str(e)}"}), 500
        
        # Mark as read
        ShareDB.mark_share_as_read(share_id, current_user_id)
        
        return jsonify({
            "share_id": share_id,
            "decrypted_secret": decrypted_secret,
            "sender_email": share.get('sender_email', 'Unknown'),
            "message": share.get('message', ''),
            "created_at": share.get('created_at', ''),
            "status": "decrypted"
        }), 200
        
    except Exception as e:
        print(f"❌ Decrypt internal share error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Decryption failed: {str(e)}"}), 500

@share_bp.route('/incoming', methods=['GET'])
@jwt_required()
def get_incoming_shares():
    """Get shares sent to current user"""
    try:
        current_user_id = get_jwt_identity()
        
        shares = ShareDB.get_incoming_shares(current_user_id)
        
        # Remove encrypted_secret from response for security
        safe_shares = []
        for share in shares:
            safe_share = share.copy()
            safe_share.pop('encrypted_secret', None)
            safe_shares.append(safe_share)
        
        return jsonify({"shares": safe_shares}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get incoming shares: {str(e)}"}), 500

@share_bp.route('/outgoing', methods=['GET'])
@jwt_required()
def get_outgoing_shares():
    """Get shares sent by current user"""
    try:
        current_user_id = get_jwt_identity()
        
        shares = ShareDB.get_outgoing_shares(current_user_id)
        
        # Remove encrypted_secret from response for security
        safe_shares = []
        for share in shares:
            safe_share = share.copy()
            safe_share.pop('encrypted_secret', None)
            safe_shares.append(safe_share)
        
        return jsonify({"shares": safe_shares}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get outgoing shares: {str(e)}"}), 500