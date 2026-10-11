"""Registers every feature blueprint. New blueprints are added here on later days."""


def register_blueprints(app):
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.dashboard import bp as dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
