import requests
import json

def test_otp_system():
    """Test OTP system end-to-end"""
    
    print("🔑 Testing OTP System")
    print("=" * 40)
    
    base_url = "http://localhost:5000/api"
    
    # Login
    login_data = {'email': 'admin@test.com', 'password': 'admin123'}
    login_response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
    
    if login_response.status_code != 200:
        print("❌ Login failed")
        return
    
    access_token = login_response.json().get('access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    print("✅ Login successful")
    
    # Test add OTP account
    print("\n🔍 Testing add OTP account...")
    test_account = {
        'issuer': 'Google',
        'account': 'testssssgmail.com',
        'secret': 'đágbadguykáhdka',  # Test secret
        'digits': 6,
        'period': 30,
        'algorithm': 'SHA1'
    }
    
    add_response = requests.post(f"{base_url}/otp/accounts", 
                                json=test_account, 
                                headers=headers, 
                                timeout=10)
    
    print(f"   Status: {add_response.status_code}")
    
    if add_response.status_code == 201:
        print("✅ OTP account added successfully")
        account_id = add_response.json().get('account_id')
        print(f"   Account ID: {account_id}")
    else:
        print("❌ Failed to add OTP account")
        print(f"   Response: {add_response.text}")
        return
    
    # Test get accounts
    print("\n🔍 Testing get OTP accounts...")
    accounts_response = requests.get(f"{base_url}/otp/accounts", headers=headers, timeout=10)
    
    if accounts_response.status_code == 200:
        accounts_data = accounts_response.json()
        accounts = accounts_data.get('accounts', [])
        print(f"✅ Found {len(accounts)} OTP accounts")
        
        for account in accounts:
            print(f"   - {account['issuer']} ({account['account']})")
    else:
        print("❌ Failed to get OTP accounts")
        return
    
    # Test generate OTPs
    print("\n🔍 Testing OTP generation...")
    generate_response = requests.get(f"{base_url}/otp/generate", headers=headers, timeout=10)
    
    if generate_response.status_code == 200:
        otp_data = generate_response.json()
        otp_accounts = otp_data.get('otp_accounts', [])
        print(f"✅ Generated {len(otp_accounts)} OTP codes")
        
        for otp in otp_accounts:
            print(f"   - {otp['issuer']}: {otp['otp_code']} (expires in {otp['time_remaining']}s)")
    else:
        print("❌ Failed to generate OTP codes")
        print(f"   Response: {generate_response.text}")
    
    # Test QR code parsing
    print("\n🔍 Testing QR code parsing...")
    test_qr_url = "otpauth://totp/Example:alice@google.com?secret=JBSWY3DPEHPK3PXP&issuer=Example"
    qr_data = {'otpauth_url': test_qr_url}
    
    qr_response = requests.post(f"{base_url}/otp/qr-parse", 
                               json=qr_data, 
                               headers=headers, 
                               timeout=10)
    
    if qr_response.status_code == 201:
        print("✅ QR code parsed successfully")
        qr_result = qr_response.json()
        parsed_data = qr_result.get('parsed_data', {})
        print(f"   Issuer: {parsed_data.get('issuer')}")
        print(f"   Account: {parsed_data.get('account')}")
    else:
        print("❌ Failed to parse QR code")
        print(f"   Response: {qr_response.text}")

if __name__ == "__main__":
    test_otp_system()