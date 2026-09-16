import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable must be set. Copy .env.example to "
        ".env and set a real value, e.g.:\n"
        '  python -c "import secrets; print(secrets.token_hex(32))"'
    )

DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
DB_PATH = os.environ.get("DB_PATH", "loja.db")
JWT_EXP_HOURS = int(os.environ.get("JWT_EXP_HOURS", "8"))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
