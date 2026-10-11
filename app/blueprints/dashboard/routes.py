from flask import redirect, render_template, url_for
from sqlalchemy import text

from app.blueprints.dashboard import bp
from app.extensions import db


@bp.get("/")
def home():
    return redirect(url_for("dashboard.index"))


@bp.get("/dashboard")
def index():
    # Placeholder page for Day 3: shows that the database connection works.
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return render_template("dashboard/index.html", db_ok=db_ok)
