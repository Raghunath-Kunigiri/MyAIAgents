"""Test login credentials to debug authentication issues"""
from werkzeug.security import check_password_hash
from webapp.models import User
from webapp import get_db

def test_login(email, password):
    """Test if login credentials work"""
    client, db = get_db()
    
    try:
        email_normalized = email.strip().lower()
        print("=" * 70)
        print(f"Testing login for: {email}")
        print(f"Normalized email: {email_normalized}")
        print("=" * 70)
        
        # Try to find user
        user = User.get_by_email(db, email_normalized)
        
        if not user:
            # Try case-insensitive search
            user_doc = db['Users'].find_one({"email": {"$regex": f"^{email_normalized}$", "$options": "i"}})
            if user_doc:
                user = User(user_doc)
                print(f"[INFO] Found user with case-insensitive search")
        
        if not user:
            print(f"[X] ERROR: User not found in database")
            print("\nAvailable users in database:")
            all_users = db['Users'].find({}, {"email": 1, "name": 1})
            for u in all_users:
                print(f"  - {u.get('email')} ({u.get('name', 'No name')})")
            return False
        
        print(f"[OK] User found!")
        print(f"  ID: {user.id}")
        print(f"  Email in DB: {user.email}")
        print(f"  Name: {user.name}")
        
        # Test password
        print(f"\nTesting password...")
        password_match = check_password_hash(user.password_hash, password)
        
        if password_match:
            print(f"[OK] PASSWORD IS CORRECT!")
            print("=" * 70)
            print("Login should work with these credentials:")
            print(f"  Email: {email_normalized} (use lowercase)")
            print(f"  Password: {password}")
            print("=" * 70)
            return True
        else:
            print(f"[X] PASSWORD DOES NOT MATCH!")
            print(f"\nThe password '{password}' does not match the stored hash.")
            print("\nTo reset password, run:")
            print(f"  python check_user_account.py {email_normalized} YOUR_NEW_PASSWORD")
            return False
            
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        client.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python test_login.py EMAIL PASSWORD")
        print("\nExample:")
        print("  python test_login.py admin@gmail.com Admin123")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    test_login(email, password)
