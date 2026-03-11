import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-12345")
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False  # We'll handle CSRF ourselves for API routes
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
    USERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "users.json")
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
