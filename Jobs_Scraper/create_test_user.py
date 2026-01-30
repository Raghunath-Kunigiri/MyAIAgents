"""
IMPORTANT: This script ONLY modifies the TEST account (test@example.com).
It will NEVER touch or modify ANY other user's credentials.
Your personal account credentials are completely safe and will NEVER be changed by this script.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import User
from webapp import get_db

# CRITICAL: This email is HARDCODED to ONLY affect the test account
# YOUR personal account is 100% safe from this script
TEST_ACCOUNT_EMAIL = "test@example.com"  # DO NOT CHANGE THIS

def create_test_user():
    client, db = get_db()
    
    # Test user credentials - PERMANENT CREDENTIALS
    # ONLY affects: test@example.com
    # YOUR account credentials are NEVER touched by this script
    email = TEST_ACCOUNT_EMAIL  # Hardcoded - cannot affect other accounts
    password = "test123"
    name = "Test User"
    
    # SAFETY CHECK: Double verify we're only touching the test account
    if email != TEST_ACCOUNT_EMAIL:
        print("ERROR: Script can only modify test@example.com account!")
        print("This is a safety feature to protect your credentials.")
        client.close()
        return
    
    # Check if user already exists
    existing_user = User.get_by_email(db, email)
    if existing_user:
        # Generate password hash to check/update
        password_hash = generate_password_hash(password)
        
        # Check if the current password already matches
        password_needs_update = not check_password_hash(existing_user.password_hash, password)
        
        # Only update password if it doesn't match
        if password_needs_update:
            existing_user.update_password(db, password_hash)
            password_msg = "Password UPDATED (was incorrect)."
        else:
            password_msg = "Password already correct (not changed)."
        
        # Update name if different
        name_changed = existing_user.name != name
        if name_changed:
            existing_user.update_profile(db, name, email, existing_user.n8n_webhook_url, existing_user.n8n_api_key)
        else:
            # Just ensure profile is correct (without changing if already correct)
            pass
        
        print("=" * 70)
        print("⚠️  IMPORTANT: This script ONLY modified test@example.com")
        print("⚠️  YOUR personal account credentials were NOT touched")
        print("=" * 70)
        print(f"Test Account Email: {email}")
        print(f"Test Account Password: {password}")
        print(f"Status: {password_msg}")
        if name_changed:
            print(f"Name: UPDATED to '{name}'")
        else:
            print(f"Name: Already set to '{name}'")
        print("=" * 70)
        print("\nYour personal credentials are safe and unchanged.")
        print("You can log in at: http://localhost:5000/login")
        print("=" * 70)
    else:
        # Create new user
        password_hash = generate_password_hash(password)
        user = User.create_user(db, email, password_hash, name)
        
        print("=" * 50)
        print("Test user created successfully!")
        print("=" * 50)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Name: {name}")
        print("=" * 50)
        print("\nYou can now log in at: http://localhost:5000/login")
        print("Or create a new account at: http://localhost:5000/register")
        print("=" * 50)
    
    client.close()

if __name__ == "__main__":
    create_test_user()
