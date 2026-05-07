import requests
import json

BASE_URL = 'http://localhost:8001/api/v1'

def run_tests():
    print("Testing Registration...")
    res = requests.post(f"{BASE_URL}/auth/register/", json={
        "email": "test2@example.com",
        "password": "password123",
        "full_name": "Test User",
        "organization_name": "Test Org 2"
    })
    
    if res.status_code != 201:
        print(f"Registration failed: {res.text}")
        # Try logging in if it already exists
        res = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": "test2@example.com",
            "password": "password123"
        })
        if res.status_code != 200:
            print(f"Login failed: {res.text}")
            return
            
    data = res.json()
    token = data['tokens']['access'] if 'tokens' in data else data['access']
    tenant_id = data.get('tenant_id')
    print(f"Logged in successfully. Tenant ID: {tenant_id}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id),
        "Content-Type": "application/json"
    }
    
    print("\nTesting GET /crm/deals/")
    res = requests.get(f"{BASE_URL}/crm/deals/", headers=headers)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}")
    
    print("\nTesting POST /crm/contacts/ (Create Button equivalent)")
    res = requests.post(f"{BASE_URL}/crm/contacts/", headers=headers, json={
        "first_name": "Test",
        "last_name": "User",
        "email": "testuser@example.com"
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}")
    
    print("\nTesting POST /crm/companies/ (Add Company equivalent)")
    res = requests.post(f"{BASE_URL}/crm/companies/", headers=headers, json={
        "name": "Acme Corp",
        "industry": "Tech",
        "annual_revenue": "1000000"
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:200]}")

if __name__ == '__main__':
    run_tests()
