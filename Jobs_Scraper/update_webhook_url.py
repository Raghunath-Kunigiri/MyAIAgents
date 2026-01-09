"""Update n8n webhook URL for a user"""
import sys
from webapp import get_db
from webapp.models import User

def update_webhook_url(email, webhook_url):
    """Update n8n webhook URL for a user"""
    client, db = get_db()
    
    try:
        user = User.get_by_email(db, email)
        if not user:
            print(f"User with email '{email}' not found.")
            print("\nAvailable users:")
            users = db['Users'].find({}, {"email": 1, "name": 1})
            for u in users:
                print(f"  - {u.get('email')} ({u.get('name', 'No name')})")
            return False
        
        user.update_profile(db, user.name, user.email, webhook_url, None)
        print(f"[OK] Webhook URL updated successfully for {user.email}!")
        print(f"     Webhook URL: {webhook_url}")
        return True
    except Exception as e:
        print(f"[ERROR] Error updating webhook URL: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_webhook_url.py <email> <webhook_url>")
        print("\nExample:")
        print('  python update_webhook_url.py test@example.com "http://54.90.110.145:5678/webhook-test/resume-tailor"')
        sys.exit(1)
    
    email = sys.argv[1]
    webhook_url = sys.argv[2]
    
    update_webhook_url(email, webhook_url)
