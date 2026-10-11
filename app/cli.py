"""Command-line commands: flask create-owner (more are added on later days)."""
import click

from app.extensions import db
from app.models import User


@click.command("create-owner")
@click.option("--name", prompt="Owner name")
@click.option("--email", prompt="Owner email")
@click.password_option(prompt="Password (at least 8 characters)", confirmation_prompt=True)
def create_owner(name, email, password):
    """Create the single owner account."""
    name = name.strip()
    email = email.strip().lower()
    if not name:
        raise click.ClickException("Name is required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise click.ClickException("Enter a valid email address.")
    if len(password) < 8:
        raise click.ClickException("Password must be at least 8 characters.")
    if db.session.query(User).count() > 0:
        raise click.ClickException("An owner account already exists.")
    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    click.echo("Owner account created for {}.".format(email))


def register_cli(app):
    app.cli.add_command(create_owner)
