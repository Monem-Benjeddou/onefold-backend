# User Management Commands

This directory contains Django management commands for managing users in the neoevents API.

## Available Commands

### `export_users`

Export all users to a CSV file with all fields.

```bash
python manage.py export_users [options]
```

This command exports all user data to a CSV file. By default, it excludes the password field for security reasons.

**Options:**

- `--output`: Output file path (default: users_export_YYYY-MM-DD.csv in current directory)
- `--roles`: Filter by user roles (e.g., --roles admin jury_member)
- `--active-only`: Export only active users (is_active=True)
- `--verified-only`: Export only email verified users
- `--query`: Filter by username, email, or fullname contains
- `--exclude-fields`: Exclude specific fields (e.g., --exclude-fields password last_login)
- `--limit`: Limit the number of users exported

**Examples:**

```bash
# Export all users to the default file (users_export_YYYY-MM-DD.csv)
python manage.py export_users

# Export to a specific file
python manage.py export_users --output=/path/to/my_users.csv

# Export only admin and jury members
python manage.py export_users --roles admin jury_member

# Export only verified users and exclude sensitive fields
python manage.py export_users --verified-only --exclude-fields password last_login date_joined

# Export users with "john" in their name or email
python manage.py export_users --query=john

# Export only the first 100 users
python manage.py export_users --limit=100
```

**Additional Information:**

- The export includes all fields from the User model except those explicitly excluded.
- Two additional calculated fields are included:
  - `total_submissions`: Number of submissions owned by the user
  - `total_team_memberships`: Number of teams the user is a member of
- Date/time fields are exported in ISO format (YYYY-MM-DDTHH:MM:SS)
- The command shows progress during export for large datasets
- Upon completion, the command reports the total number of users exported and the file size 