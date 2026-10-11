import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def owner(app):
    user = User(name="Test Owner", email="owner@test.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def logged_in_client(client, owner):
    client.post(
        "/login",
        data={"email": "owner@test.com", "password": "password123"},
        follow_redirects=True,
    )
    return client
