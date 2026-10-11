from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.blueprints.auth import bp
from app.blueprints.auth.forms import LoginForm
from app.extensions import db
from app.models import User


def _safe_next(target):
    """Only allow redirects to paths inside this site (blocks open-redirect tricks)."""
    if not target:
        return None
    parts = urlparse(target)
    if parts.scheme or parts.netloc:
        return None
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    return target


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.query(User).filter_by(email=email).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(_safe_next(request.args.get("next")) or url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
