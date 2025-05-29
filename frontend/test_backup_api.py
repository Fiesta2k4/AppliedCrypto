# Create this test file để debug API calls
import requests
import json

def get_access_token():
    """Get access token by login"""
    try:
        base_url = "http://localhost:5000/api"
        
        # Get credentials from user
        email = input("Enter email: ").strip()
        password = input("Enter password: ").strip()
        
        print(f"🔍 Logging in as: {email}")
        
        # Login request
        login_data = {
            "email": email,
            "password": password
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        print(f"🔍 Login response ({response.status_code}): {response.json()}")
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get('access_token')
            
            if access_token:
                print(f"✅ Login successful!")
                print(f"🔍 Access token: {access_token[:50]}...")
                return access_token
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Login failed: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_backup_api():
    """Test backup API endpoints directly"""
    
    print("=== Testing Backup API ===")
    
    # Get real access token
    access_token = get_access_token()
    
    if not access_token:
        print("❌ Cannot proceed without access token")
        return
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = "http://localhost:5000/api"
    
    # Test 1: Debug endpoint
    print("\n🔍 Testing debug endpoint...")
    try:
        response = requests.get(f"{base_url}/backup/debug", headers=headers)
        print(f"Debug Response ({response.status_code}):")
        print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Debug Error: {e}")
    
    # Test 2: List backups
    print("\n🔍 Testing list backups...")
    try:
        response = requests.get(f"{base_url}/backup/list", headers=headers)
        print(f"List Response ({response.status_code}):")
        result = response.json()
        print(json.dumps(result, indent=2))
        
        # Analyze the result
        if 'backups' in result:
            backups = result['backups']
            print(f"\n📊 Found {len(backups)} backups:")
            for i, backup in enumerate(backups):
                print(f"  {i+1}. {backup.get('name')} (ID: {backup.get('id')})")
        
    except Exception as e:
        print(f"List Error: {e}")
    
    # Test 3: Get vault entries for comparison
    print("\n🔍 Testing vault entries...")
    try:
        response = requests.get(f"{base_url}/vault/", headers=headers)
        vault_data = response.json()
        print(f"Vault Response ({response.status_code}):")
        print(f"Entry count = {vault_data.get('count', 0)}")
        
        if 'entries' in vault_data:
            entries = vault_data['entries']
            print(f"📊 Vault has {len(entries)} entries:")
            for i, entry in enumerate(entries):
                name = entry.get('metadata', {}).get('name', 'Unnamed')
                print(f"  {i+1}. {name} (ID: {entry.get('id')})")
                
    except Exception as e:
        print(f"Vault Error: {e}")

if __name__ == "__main__":
    test_backup_api()