"""StockSense application factory."""
from flask import Flask, jsonify, request
from flask_login import current_user

from app.config import get_config
from app.extensions import csrf, db, login_manager, migrate
from app.utils.formatting import ist, rupees

# Pages anyone can open without signing in.
PUBLIC_ENDPOINTS = {"auth.login", "healthz", "static"}


def create_app(config_name=None):
    app = Flask(__name__)
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    if config_class.__name__ == "ProductionConfig" and app.config["SECRET_KEY"] == "dev-only-secret-change-me":
        raise RuntimeError("SECRET_KEY must be set in production.")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = None

    # Import models so the database tools can see every table.
    from app import models  # noqa: F401

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(models.User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.path.startswith("/api/"):
            return jsonify(error={"code": "UNAUTHORIZED", "message": "Sign in required."}), 401
        from flask import redirect, url_for

        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))

    @app.before_request
    def require_login():
        if request.endpoint is None or request.endpoint in PUBLIC_ENDPOINTS:
            return None
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        return None

    app.add_template_filter(rupees, "rupees")
    app.add_template_filter(ist, "ist")

    from app.blueprints import register_blueprints

    register_blueprints(app)

    @app.get("/healthz")
    def healthz():
        return "ok", 200, {"Content-Type": "text/plain; charset=utf-8"}

    from app.cli import register_cli

    register_cli(app)

    return app
