"""Quick script to switch between test and production webhook URLs"""
import sys
from webapp import get_db
from webapp.models import User

# Webhook URLs
TEST_WEBHOOK = "http://54.90.110.145:5678/webhook-test/resume-tailor"
PRODUCTION_WEBHOOK = "http://54.90.110.145:5678/webhook/resume-tailor"

def switch_webhook(email, mode='test'):
    """Switch webhook URL for a user"""
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
        
        if mode.lower() == 'test':
            webhook_url = TEST_WEBHOOK
            mode_name = "TEST"
        elif mode.lower() in ['prod', 'production']:
            webhook_url = PRODUCTION_WEBHOOK
            mode_name = "PRODUCTION"
        else:
            print(f"Invalid mode: {mode}")
            print("Use 'test' or 'prod'/'production'")
            return False
        
        user.update_profile(db, user.name, user.email, webhook_url, None)
        print(f"[OK] Webhook URL updated to {mode_name} mode for {user.email}!")
        print(f"     Webhook URL: {webhook_url}")
        print(f"\nNote: Make sure your n8n workflow is active and configured for this webhook.")
        return True
    except Exception as e:
        print(f"[ERROR] Error updating webhook URL: {e}")
        return False
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python switch_webhook.py <email> <test|prod>")
        print("\nExamples:")
        print("  python switch_webhook.py test@example.com test")
        print("  python switch_webhook.py test@example.com prod")
        print("\nWebhook URLs:")
        print(f"  TEST:       {TEST_WEBHOOK}")
        print(f"  PRODUCTION: {PRODUCTION_WEBHOOK}")
        sys.exit(1)
    
    email = sys.argv[1]
    mode = sys.argv[2]
    
    switch_webhook(email, mode)
