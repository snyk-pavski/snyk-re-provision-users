import requests
import json
import os
import sys
import time

# Configuration
SNYK_TOKEN = os.getenv('SNYK_TOKEN')
API_BASE = "https://api.snyk.io/v1"

if not SNYK_TOKEN:
    print("Error: SNYK_TOKEN environment variable is not set.")
    sys.exit(1)

HEADERS = {
    'Authorization': f'token {SNYK_TOKEN}',
    'Content-Type': 'application/json'
}

def provision_user(org_id, email, role_name, role_public_id):
    """
    Provisions a user to an org using rolePublicId if available.
    """
    url = f"{API_BASE}/org/{org_id}/provision"
    
    payload = {
        "email": email
    }

    # Prioritize rolePublicId as requested
    if role_public_id:
        payload["rolePublicId"] = role_public_id
    else:
        # Fallback to legacy role name if ID is missing
        payload["role"] = role_name
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        
        if response.status_code in [200, 201]:
            print(f"    [OK] Provisioned {email}")
            return True
        elif response.status_code == 409:
             print(f"    [SKIP] User {email} already exists in this org.")
             return True
        else:
            print(f"    [FAIL] {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"    [ERROR] Exception occurred: {str(e)}")
        return False

def process_provisioning_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("File not found.")
        sys.exit(1)

    group_id = data.get('group_id')
    users = data.get('users', [])
    
    print(f"Starting provisioning for Group ID: {group_id}")
    print(f"Total users to process: {len(users)}")
    print("-" * 40)

    for user in users:
        email = user.get('email')
        memberships = user.get('memberships', [])
        
        if not email:
            print(f"Skipping user ID {user.get('id')} (No email found)")
            continue

        print(f"Processing User: {email}")
        
        for membership in memberships:
            org_id = membership['org_id']
            org_name = membership.get('org_name', 'Unknown Org')
            role_name = membership.get('role')
            role_public_id = membership.get('role_public_id')
            
            print(f"  -> Org: {org_name}")
            
            # API Rate limit safety buffer
            # time.sleep(0.2) 
            
            provision_user(org_id, email, role_name, role_public_id)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python provision_user_in_a_group.py <path_to_json_file>")
        sys.exit(1)
        
    json_file = sys.argv[1]
    process_provisioning_file(json_file)