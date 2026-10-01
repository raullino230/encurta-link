from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
limiter = Limiter(key_func = get_remote_address)
csrf = CSRFProtect()

def create_app(config_teste=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")

    if config_teste is not None:
        app.config.update(config_teste)

    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)
    app.config.setdefault("RATELIMIT_STORAGE_URI", app.config.get("REDIS_URL") or "memory://")
    limiter.init_app(app)
    csrf.init_app(app)

    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    
    
    from app.routes.links import links_bp
    app.register_blueprint(links_bp)

    from app.routes.redirect import redirect_bp
    app.register_blueprint(redirect_bp)

    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.frontend.routes_fronend import frontend_bp
    app.register_blueprint(frontend_bp)

    return app
