# Snyk User Domain Migration Tools

Python scripts for migrating Snyk users from one email domain to another. Exports users from a Group with all their organization memberships and roles, allowing you to update email addresses and re-provision them automatically.

## Prerequisites

* Python 3.x
* Snyk API Token with Group Admin permissions

## Setup

```bash
pip install requests
export SNYK_TOKEN='your-snyk-api-token'
```

## Workflow

### 1. Export Users

```bash
python get_current_users_in_groups.py <group_id_1>,<group_id_2>
```

Generates a JSON file per group containing all users, their organizations, and roles with UUIDs.

### 2. Update Email Domains

Edit the generated JSON file and replace email domains:
- Find: `@old-domain.com`
- Replace: `@new-domain.com`

**Note:** Only modify `email` fields. Do not change `org_id`, `role`, or `role_public_id`.

### 3. Provision Users

```bash
python provision_user_in_a_group.py GroupName.json
```

Adds users to their organizations with the correct roles. Safely skips users who already exist.

## JSON Structure

```json
{
  "group_id": "group-uuid",
  "group_name": "My Group",
  "users": [
    {
      "id": "user-uuid",
      "name": "John Doe",
      "username": "jdoe",
      "email": "john.doe@new-domain.com",
      "memberships": [
        {
          "org_id": "org-uuid",
          "org_name": "Backend Team",
          "role": "Org Admin",
          "role_public_id": "role-uuid"
        }
      ]
    }
  ]
}
```

## Notes

* **Rate Limits:** Uncomment `time.sleep(0.2)` in provision script if you hit 429 errors
* **SSO:** Ensure new emails match your Identity Provider
* Safe to re-run if interrupted