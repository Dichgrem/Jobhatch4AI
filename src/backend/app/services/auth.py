import json
import hashlib
import secrets
from pathlib import Path

from app.config import DATA_DIR

USERS_FILE = Path(DATA_DIR) / "users.json"

if not USERS_FILE.exists():
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    default_admin = {
        "username": "admin",
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
    }
    USERS_FILE.write_text(json.dumps([default_admin], indent=2, ensure_ascii=False))


def load_users() -> list[dict]:
    return json.loads(USERS_FILE.read_text())


def save_users(users: list[dict]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2, ensure_ascii=False))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_hex(32)


tokens: dict[str, str] = {}


def authenticate(username: str, password: str) -> str | None:
    users = load_users()
    hashed = hash_password(password)
    for u in users:
        if u["username"] == username and u["password"] == hashed:
            token = generate_token()
            tokens[token] = username
            return token
    return None


def register(username: str, password: str) -> str | None:
    users = load_users()
    if any(u["username"] == username for u in users):
        return None
    users.append(
        {
            "username": username,
            "password": hash_password(password),
            "role": "user",
        }
    )
    save_users(users)
    token = generate_token()
    tokens[token] = username
    return token


def get_username_by_token(token: str) -> str | None:
    return tokens.get(token)


def remove_token(token: str) -> None:
    tokens.pop(token, None)
