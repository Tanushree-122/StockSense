from app.models import User


def test_healthz_is_public(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.data == b"ok"


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_root_redirects_when_signed_out(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_login_success_and_dashboard(client, owner):
    response = client.post(
        "/login",
        data={"email": "OWNER@test.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Welcome, Test Owner" in response.data
    assert b"Connected" in response.data


def test_login_wrong_password(client, owner):
    response = client.post(
        "/login", data={"email": "owner@test.com", "password": "wrong-password"}
    )
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data


def test_login_unknown_email(client, owner):
    response = client.post(
        "/login", data={"email": "nobody@test.com", "password": "password123"}
    )
    assert b"Invalid email or password." in response.data


def test_logout_requires_login_then_signs_out(logged_in_client):
    response = logged_in_client.post("/logout", follow_redirects=True)
    assert b"signed out" in response.data
    again = logged_in_client.get("/dashboard")
    assert again.status_code == 302


def test_next_redirect_is_followed_only_when_safe(client, owner):
    safe = client.post(
        "/login?next=/dashboard",
        data={"email": "owner@test.com", "password": "password123"},
    )
    assert safe.headers["Location"].endswith("/dashboard")
    client.post("/logout")
    unsafe = client.post(
        "/login?next=https://evil.example.com",
        data={"email": "owner@test.com", "password": "password123"},
    )
    assert "evil.example.com" not in unsafe.headers["Location"]


def test_api_returns_401_json_when_signed_out(app):
    @app.get("/api/ping")
    def ping():
        return "pong"

    client = app.test_client()
    response = client.get("/api/ping")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_create_owner_command(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["create-owner"],
        input="Asha Rao\nasha@store.com\nstrongpass1\nstrongpass1\n",
    )
    assert result.exit_code == 0, result.output
    assert "Owner account created" in result.output
    assert User.query.filter_by(email="asha@store.com").first() is not None
    second = runner.invoke(
        args=["create-owner"],
        input="Other\nother@store.com\nstrongpass1\nstrongpass1\n",
    )
    assert second.exit_code != 0
    assert "already exists" in second.output
