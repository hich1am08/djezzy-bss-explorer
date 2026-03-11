import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app.config import Config

class UserService:
    @staticmethod
    def _save_users(users):
        with open(Config.USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)

    @staticmethod
    def get_users():
        if not os.path.exists(Config.USERS_FILE):
            default_users = {
                "admin": {
                    "password_hash": generate_password_hash("admin"),
                    "role": "admin"
                }
            }
            UserService._save_users(default_users)
            return default_users
        with open(Config.USERS_FILE, 'r') as f:
            return json.load(f)

    @staticmethod
    def authenticate(username, password):
        users = UserService.get_users()
        user = users.get(username)
        if user and check_password_hash(user['password_hash'], password):
            return {"username": username, "role": user.get('role', 'user')}
        return None

    @staticmethod
    def list_users():
        """List all users (without password hashes)."""
        users = UserService.get_users()
        return [{"username": u, "role": d.get("role", "user")} for u, d in users.items()]

    @staticmethod
    def create_user(username, password, role="user"):
        """Create a new user. Returns True on success."""
        users = UserService.get_users()
        if username in users:
            return False, "User already exists"
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        if not password or len(password) < 4:
            return False, "Password must be at least 4 characters"
        if role not in ("admin", "user"):
            role = "user"
        users[username] = {
            "password_hash": generate_password_hash(password),
            "role": role
        }
        UserService._save_users(users)
        return True, "User created"

    @staticmethod
    def change_password(username, new_password):
        """Change a user's password."""
        users = UserService.get_users()
        if username not in users:
            return False, "User not found"
        if not new_password or len(new_password) < 4:
            return False, "Password must be at least 4 characters"
        users[username]["password_hash"] = generate_password_hash(new_password)
        UserService._save_users(users)
        return True, "Password changed"

    @staticmethod
    def delete_user(username):
        """Delete a user (cannot delete last admin)."""
        users = UserService.get_users()
        if username not in users:
            return False, "User not found"
        # Cannot delete if it's the last admin
        admin_count = sum(1 for u in users.values() if u.get("role") == "admin")
        if users[username].get("role") == "admin" and admin_count <= 1:
            return False, "Cannot delete the last admin"
        del users[username]
        UserService._save_users(users)
        return True, "User deleted"
