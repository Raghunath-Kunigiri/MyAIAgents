"""Check and optionally reset a user account - SAFE for your personal account"""
from werkzeug.security import generate_password_hash, check_password_hash
from webapp.models import User
from webapp import get_db

def check_user_account(email, new_password=None):
    """
    Check if a user account exists and optionally reset its password.
    
    Args:
        email: Email address to check
        new_password: Optional new password to set (if None, just checks)
    """
    client, db = get_db()
    
    try:
        # Normalize email
        email = email.strip().lower()
        
        # Find user
        user = User.get_by_email(db, email)
        
        if not user:
            print("=" * 70)
            print(f"[X] Account NOT FOUND: {email}")
            print("=" * 70)
            print("\nPossible reasons:")
            print("  1. The account was never created")
            print("  2. The email is misspelled")
            print("  3. The account was deleted")
            print("\nYou can create a new account at: http://localhost:5000/register")
            print("=" * 70)
            return False
        
        # Account exists
        print("=" * 70)
        print(f"[OK] Account FOUND: {email}")
        print("=" * 70)
        print(f"Account ID: {user.id}")
        print(f"Name: {user.name}")
        print(f"Email: {user.email}")
        print(f"Created: {user.created_at}")
        
        # If new password provided, update it
        if new_password:
            if len(new_password) < 6:
                print("\n[X] ERROR: Password must be at least 6 characters long")
                return False
            
            new_password_hash = generate_password_hash(new_password)
            user.update_password(db, new_password_hash)
            
            print("\n" + "=" * 70)
            print("[OK] PASSWORD RESET SUCCESSFUL!")
            print("=" * 70)
            print(f"Email: {email}")
            print(f"New Password: {new_password}")
            print("=" * 70)
            print("\nYou can now log in at: http://localhost:5000/login")
            print("=" * 70)
            return True
        else:
            print("\n" + "=" * 70)
            print("[INFO] Account exists, but password was not reset.")
            print("=" * 70)
            print("To reset password, run:")
            print(f"  python check_user_account.py {email} YOUR_NEW_PASSWORD")
            print("=" * 70)
            return True
            
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Check account:  python check_user_account.py EMAIL")
        print("  Reset password: python check_user_account.py EMAIL NEW_PASSWORD")
        print("\nExample:")
        print("  python check_user_account.py admin@gmail.com")
        print("  python check_user_account.py admin@gmail.com MyNewPassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2] if len(sys.argv) > 2 else None
    
    check_user_account(email, new_password)
