"""Normalize all user emails to lowercase to prevent case-sensitivity issues"""
from webapp import get_db

def normalize_user_emails():
    """Normalize all user emails to lowercase in the database"""
    client, db = get_db()
    
    try:
        users_collection = db['Users']
        
        # Get all users
        users = list(users_collection.find({}))
        
        print("=" * 70)
        print("Normalizing user emails to lowercase...")
        print("=" * 70)
        
        updated_count = 0
        for user in users:
            current_email = user.get('email', '')
            normalized_email = current_email.strip().lower()
            
            if current_email != normalized_email:
                users_collection.update_one(
                    {"_id": user['_id']},
                    {"$set": {"email": normalized_email}}
                )
                print(f"[UPDATED] {current_email} -> {normalized_email}")
                updated_count += 1
            else:
                print(f"[OK] {current_email} (already normalized)")
        
        print("=" * 70)
        print(f"Total users checked: {len(users)}")
        print(f"Emails normalized: {updated_count}")
        print("=" * 70)
        print("\nAll user emails are now normalized to lowercase.")
        print("Login should work regardless of case you type.")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[X] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    normalize_user_emails()
