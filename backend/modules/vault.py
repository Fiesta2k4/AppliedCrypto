from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.helpers import VaultDB
import traceback

vault_bp = Blueprint('vault', __name__)

@vault_bp.route('/', methods=['POST'])
@jwt_required()
def create_entry():
    """Create new vault entry"""
    try:
        current_user_id = get_jwt_identity()  # ✅ This is user_id, not email
        data = request.get_json()
        
        print(f"🔐 Creating vault entry for user: {current_user_id}")
        
        # Validation
        required_fields = ['iv', 'ciphertext', 'tag']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400
        
        # Create entry
        entry = VaultDB.create_entry(
            user_id=current_user_id,  # ✅ Fixed: use user_id instead of user_email
            iv=data.get('iv'),
            ciphertext=data.get('ciphertext'),
            tag=data.get('tag'),
            metadata=data.get('metadata', {})
        )
        
        if entry:
            print(f"✅ Vault entry created: {entry['id']}")
            return jsonify({
                "message": "Entry created successfully",
                "id": entry['id'],
                "entry": entry
            }), 201
        else:
            return jsonify({"error": "Failed to create entry"}), 500
        
    except Exception as e:
        print(f"❌ Create entry error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to create entry: {str(e)}"}), 500

@vault_bp.route('/', methods=['GET'])
@jwt_required()
def get_entries():
    """Get all vault entries for user"""
    try:
        current_user_id = get_jwt_identity()
        
        print(f"📋 Getting vault entries for user: {current_user_id}")
        
        entries = VaultDB.get_user_entries(current_user_id)
        
        print(f"📊 Found {len(entries)} entries")
        
        return jsonify({
            "entries": entries,
            "count": len(entries)
        }), 200
        
    except Exception as e:
        print(f"❌ Get entries error: {e}")
        return jsonify({"error": f"Failed to get entries: {str(e)}"}), 500

@vault_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get vault statistics"""
    try:
        current_user_id = get_jwt_identity()
        
        stats = VaultDB.get_stats(current_user_id)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": f"Failed to get stats: {str(e)}"}), 500

@vault_bp.route('/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_entry(entry_id):
    """Delete vault entry"""
    try:
        current_user_id = get_jwt_identity()
        
        print(f"🗑️ Deleting vault entry {entry_id} for user: {current_user_id}")
        
        # Verify entry belongs to user and delete
        success = VaultDB.delete_entry(entry_id, current_user_id)
        
        if success:
            print(f"✅ Entry {entry_id} deleted successfully")
            return jsonify({
                "message": "Entry deleted successfully",
                "success": True
            }), 200
        else:
            return jsonify({"error": "Entry not found or access denied"}), 404
        
    except Exception as e:
        print(f"❌ Delete entry error: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Failed to delete entry: {str(e)}"}), 500