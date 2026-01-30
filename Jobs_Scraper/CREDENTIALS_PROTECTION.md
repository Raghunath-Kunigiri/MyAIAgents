# 🔒 CREDENTIALS PROTECTION GUARANTEE

## YOUR CREDENTIALS ARE PROTECTED

This document explains how your personal credentials are protected and will NEVER be automatically changed.

## ✅ SAFE OPERATIONS (Will NOT Change Your Password)

1. **Profile Updates** (`/profile` route)
   - Updates name, email, n8n_webhook_url, n8n_api_key
   - **NEVER touches your password**

2. **Login Process**
   - Only validates your password
   - **NEVER changes your password**

3. **All Job Management Routes**
   - Manage jobs, applications, resumes
   - **NEVER touch user credentials**

4. **Session Management**
   - Updates session tokens for security
   - **NEVER changes passwords**

## ⚠️ PASSWORD CAN ONLY BE CHANGED BY YOU

Your password can ONLY be changed in these specific ways:

1. **You explicitly change it** via `/profile` → "Change Password" form
   - Requires: You must be logged in AND provide your current password
   - This is the ONLY user-facing way to change passwords

2. **Test Account Script** (`create_test_user.py`)
   - **ONLY affects**: `test@example.com`
   - **NEVER touches**: Your personal account
   - **Safety**: Hardcoded to ONLY modify test@example.com

## 🛡️ PROTECTION MECHANISMS

1. **`create_test_user.py` Script**
   - Hardcoded to ONLY touch `test@example.com`
   - Contains safety check that prevents modifying other accounts
   - Will NOT run automatically - must be manually executed

2. **`update_profile()` Method**
   - Explicitly does NOT include password_hash in updates
   - Only updates: name, email, n8n_webhook_url, n8n_api_key
   - Password field is NEVER included in profile updates

3. **No Automatic Password Resets**
   - No scheduled tasks
   - No webhooks that change passwords
   - No background processes

## 📝 SUMMARY

**YOUR CREDENTIALS ARE SAFE:**
- ✅ Your password is stored securely (hashed) in MongoDB
- ✅ Your password can ONLY be changed by you (via profile page)
- ✅ Test scripts ONLY affect test@example.com
- ✅ No automatic processes will modify your credentials
- ✅ Profile updates NEVER touch passwords

**The ONLY way your password changes:**
1. You manually change it via the profile page (requires current password)
2. OR if you're using test@example.com, the test script might reset it

**If you're using your own account (not test@example.com):**
- Your credentials are 100% safe
- They will NEVER be automatically changed
- They will persist unless YOU explicitly change them

---
*Last Updated: Credentials protection system verified and documented*
