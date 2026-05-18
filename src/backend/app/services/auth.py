import hashlib
import secrets

from app.services.database import get_db, init_db

init_db()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token() -> str:
    return secrets.token_hex(32)


def authenticate(username: str, password: str) -> str | None:
    conn = get_db()
    hashed = hash_password(password)
    row = conn.execute(
        "SELECT username FROM users WHERE username = ? AND password_hash = ?",
        (username, hashed),
    ).fetchone()
    if not row:
        conn.close()
        return None
    token = generate_token()
    conn.execute(
        "INSERT INTO auth_tokens (token, username) VALUES (?, ?)",
        (token, username),
    )
    conn.commit()
    conn.close()
    return token


def register(username: str, password: str) -> str | None:
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
            (username, hash_password(password)),
        )
        conn.commit()
    except Exception:
        conn.close()
        return None
    token = generate_token()
    conn.execute(
        "INSERT INTO auth_tokens (token, username) VALUES (?, ?)",
        (token, username),
    )
    conn.commit()
    conn.close()
    return token


def get_username_by_token(token: str) -> str | None:
    conn = get_db()
    row = conn.execute(
        "SELECT username FROM auth_tokens WHERE token = ?", (token,)
    ).fetchone()
    conn.close()
    return row["username"] if row else None


def remove_token(token: str) -> None:
    conn = get_db()
    conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()
