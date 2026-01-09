"""Create a test user for development"""
from werkzeug.security import generate_password_hash
from webapp.models import User
from webapp import get_db

def create_test_user():
    client, db = get_db()
    
    # Test user credentials
    email = "test@example.com"
    password = "test123"
    name = "Test User"
    
    # Check if user already exists
    existing_user = User.get_by_email(db, email)
    if existing_user:
        print(f"User with email '{email}' already exists!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        client.close()
        return
    
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
