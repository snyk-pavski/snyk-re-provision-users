import requests
import json
import os
import sys
import argparse

# Configuration
SNYK_TOKEN = os.getenv('SNYK_TOKEN')
API_BASE = "https://api.snyk.io/v1"
REST_API_BASE = "https://api.snyk.io/rest"
REST_API_VERSION = "2024-11-04"  # Using GA version instead of beta

if not SNYK_TOKEN:
    print("Error: SNYK_TOKEN environment variable is not set.")
    sys.exit(1)

HEADERS = {
    'Authorization': f'token {SNYK_TOKEN}',
    'Content-Type': 'application/json'
}

REST_HEADERS = {
    'Authorization': f'token {SNYK_TOKEN}',
    'Content-Type': 'application/vnd.api+json'
}

def get_group_data(group_id):
    """
    Fetches the group name and all organizations within it.
    """
    print(f"Fetching data for Group ID: {group_id}...")
    url = f"{API_BASE}/group/{group_id}/orgs"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"Failed to fetch group {group_id}: {response.text}")
        return None, []

    data = response.json()
    group_name = data.get('name', group_id)
    orgs = data.get('orgs', [])

    print(f"Successfully fetched group: '{group_name}' (ID: {group_id})")
    print(f"Found {len(orgs)} organization(s) in this group")

    return group_name, orgs

def process_group(group_id):
    group_name, orgs = get_group_data(group_id)

    if not orgs:
        print(f"No organizations found for group {group_id} (or request failed).")
        return

    clean_group_name = "".join(x for x in group_name if x.isalnum() or x in "._- ")
    filename = f"{clean_group_name}.json"

    print(f"Processing Group: '{group_name}' -> Output: {filename}")

    users_map = {}

    for org in orgs:
        org_id = org['id']
        org_name = org['name']
        print(f"  Processing Org: {org_name}")

        # Call the REST API memberships endpoint
        url = f"{REST_API_BASE}/orgs/{org_id}/memberships?version={REST_API_VERSION}"
        response = requests.get(url, headers=REST_HEADERS)

        if response.status_code != 200:
            print(f"  Warning: Failed to fetch memberships for org {org_id} ({response.status_code})")
            print(f"  URL: {url}")
            print(f"  Response: {response.text[:200]}")
            continue

        response_data = response.json()
        memberships_data = response_data.get('data', [])

        # Process each membership
        for membership in memberships_data:
            relationships = membership.get('relationships', {})

            # Get user data from relationship (embedded directly)
            user_data = relationships.get('user', {}).get('data', {})
            user_id = user_data.get('id')
            user_attrs = user_data.get('attributes', {})

            if not user_id:
                continue

            # Get role data from relationship (embedded directly)
            role_data = relationships.get('role', {}).get('data', {})
            role_public_id = role_data.get('id')
            role_attrs = role_data.get('attributes', {})
            role_name = role_attrs.get('name', 'unknown')

            # Add or update user in map
            if user_id not in users_map:
                users_map[user_id] = {
                    "id": user_id,
                    "name": user_attrs.get('name'),
                    "username": user_attrs.get('username'),
                    "email": user_attrs.get('email'),
                    "memberships": []
                }

            # Store the role information with UUID
            users_map[user_id]["memberships"].append({
                "org_id": org_id,
                "org_name": org_name,
                "role": role_name,
                "role_public_id": role_public_id
            })

    output_data = {
        "group_id": group_id,
        "group_name": group_name,
        "users": list(users_map.values())
    }

    with open(filename, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"SUCCESS: Data for group '{group_name}' written to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export Snyk Group Users')
    parser.add_argument('group_ids', help='Comma separated list of Group IDs')
    args = parser.parse_args()

    group_ids_list = [g.strip() for g in args.group_ids.split(',')]

    print(f"========================================")
    print(f"Processing {len(group_ids_list)} group(s)")
    print(f"Group ID(s) provided: {', '.join(group_ids_list)}")
    print(f"========================================\n")

    for gid in group_ids_list:
        print(f">>> Starting processing for Group ID: {gid}")
        process_group(gid)
        print()  # Add blank line between groups
