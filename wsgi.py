"""Entry point used by `flask` commands and by gunicorn on the host."""
from app import create_app

app = create_app()
