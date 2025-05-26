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

@share_bp.route('/incoming', methods=['GET'])
@jwt_required()
def get_incoming_shares():
    """Get shares sent to current user"""
    try:
        current_user_id = get_jwt_identity()
        
        shares = ShareDB.get_user_shares(current_user_id, sent=False, received=True)
        
        # Remove encrypted_secret from response for security
        safe_shares = []
        for share in shares:
            safe_share = share.copy()
            safe_share.pop('encrypted_secret', None)
            safe_shares.append(safe_share)
        
        return jsonify({"shares": safe_shares}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get shares: {str(e)}"}), 500

@share_bp.route('/outgoing', methods=['GET'])
@jwt_required()
def get_outgoing_shares():
    """Get shares sent by current user"""
    try:
        current_user_id = get_jwt_identity()
        
        shares = ShareDB.get_user_shares(current_user_id, sent=True, received=False)
        
        # Remove encrypted_secret from response
        safe_shares = []
        for share in shares:
            safe_share = share.copy()
            safe_share.pop('encrypted_secret', None)
            safe_shares.append(safe_share)
        
        return jsonify({"shares": safe_shares}), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get shares: {str(e)}"}), 500

# Note: Accept/Reject functionality requires frontend to handle RSA decryption
# For now, simplified to just getting share lists