from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.config import VaultDB

vault_bp = Blueprint('vault', __name__)

@vault_bp.route('/', methods=['GET'])
@jwt_required()
def get_vault_entries():
    """Get all vault entries for user"""
    try:
        user_id = get_jwt_identity()
        entries = VaultDB.get_user_entries(user_id)
        
        return jsonify({
            'entries': entries,
            'count': len(entries)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/', methods=['POST'])
@jwt_required()
def create_vault_entry():
    """Create new vault entry"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['iv', 'ciphertext', 'tag']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create entry
        entry = VaultDB.create_entry(
            user_id=user_id,
            iv=data['iv'],
            ciphertext=data['ciphertext'],
            tag=data['tag'],
            metadata=data.get('metadata', {})
        )
        
        return jsonify({
            'id': entry['id'],
            'created_at': entry['created_at'],
            'message': 'Entry created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/<entry_id>', methods=['DELETE'])
@jwt_required()
def delete_vault_entry(entry_id):
    """Delete vault entry"""
    try:
        user_id = get_jwt_identity()
        
        if VaultDB.delete_entry(entry_id, user_id):
            return jsonify({'message': 'Entry deleted successfully'})
        else:
            return jsonify({'error': 'Entry not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_vault_stats():
    """Get vault statistics"""
    try:
        user_id = get_jwt_identity()
        entries = VaultDB.get_user_entries(user_id)
        
        # Count by type
        types = {}
        for entry in entries:
            entry_type = entry['metadata'].get('type', 'unknown')
            types[entry_type] = types.get(entry_type, 0) + 1
        
        return jsonify({
            'total_entries': len(entries),
            'types': types
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500