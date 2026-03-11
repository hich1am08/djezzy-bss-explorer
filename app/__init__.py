from flask import Flask
from app.config import Config
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

# In-memory dictionary for Pandas Dataframes
DATA_STORE = {}

def create_app():
    app = Flask(__name__, static_folder="../", static_url_path="")
    app.config.from_object(Config)
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max upload

    csrf.init_app(app)

    # Register Blueprints
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # Load data in a background thread to prevent startup timeouts
    import threading
    def bg_load():
        with app.app_context():
            from app.services.data_loader import load_all_data
            load_all_data()
    
    thread = threading.Thread(target=bg_load)
    thread.daemon = True
    thread.start()

    return app

