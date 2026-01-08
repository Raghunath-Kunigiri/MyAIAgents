from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime
import secrets

class User(UserMixin):
    def __init__(self, user_doc):
        self.id = str(user_doc['_id'])
        self.email = user_doc['email']
        self.password_hash = user_doc['password_hash']
        self.name = user_doc.get('name', 'User')
        self.session_token = user_doc.get('session_token')
        self.n8n_webhook_url = user_doc.get('n8n_webhook_url', '')
        self.n8n_api_key = user_doc.get('n8n_api_key', '')
        self.created_at = user_doc.get('created_at', datetime.now())

    @staticmethod
    def get_by_id(db, user_id):
        try:
            user_doc = db['Users'].find_one({"_id": ObjectId(user_id)})
            if user_doc:
                return User(user_doc)
        except:
            pass
        return None

    @staticmethod
    def get_by_email(db, email):
        user_doc = db['Users'].find_one({"email": email})
        if user_doc:
            return User(user_doc)
        return None

    @staticmethod
    def create_user(db, email, password_hash, name):
        new_user = {
            "email": email,
            "password_hash": password_hash,
            "name": name,
            "created_at": datetime.now(),
            "session_token": secrets.token_urlsafe(32)
        }
        result = db['Users'].insert_one(new_user)
        new_user['_id'] = result.inserted_id
        return User(new_user)

    def update_session_token(self, db):
        new_token = secrets.token_urlsafe(32)
        db['Users'].update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"session_token": new_token}}
        )
        self.session_token = new_token
        return new_token

    def update_password(self, db, new_password_hash):
        db['Users'].update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"password_hash": new_password_hash}}
        )
        self.password_hash = new_password_hash

    def update_profile(self, db, name, email=None, n8n_webhook_url=None, n8n_api_key=None):
        update_doc = {"name": name}
        if email:
            update_doc["email"] = email
        if n8n_webhook_url is not None:
            update_doc["n8n_webhook_url"] = n8n_webhook_url
        if n8n_api_key is not None:
            update_doc["n8n_api_key"] = n8n_api_key
            
        db['Users'].update_one(
            {"_id": ObjectId(self.id)},
            {"$set": update_doc}
        )
        self.name = name
        if email:
            self.email = email
        if n8n_webhook_url is not None:
            self.n8n_webhook_url = n8n_webhook_url
        if n8n_api_key is not None:
            self.n8n_api_key = n8n_api_key
