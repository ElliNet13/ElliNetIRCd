from importlib.resources import files
from argon2 import PasswordHasher
from typing import Optional
from pathlib import Path
import sqlite3
import time

DATABASE_PATH = Path("accounts.db")
password_hasher = PasswordHasher()

class UserNotFoundError(Exception):
    """Raised when a requested user does not exist."""

class UserAlreadyExistsError(Exception):
    """Raised when a operation is attempted on a user that already exists that requires the user to not exist."""

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.autocommit = True
    conn.cursor().execute(files("ellinetircd")
    .joinpath("sql", "accounts.sql")
    .read_text(encoding="utf-8"))
    return conn

def add_user(cur: sqlite3.Cursor, name: str, password: str, email: Optional[str] = None):
    if does_user_exist(cur, name):
        raise UserAlreadyExistsError
    cur.execute(
        "INSERT INTO accounts (name, password_hash, email, registered_at) VALUES (?, ?, ?, ?)",
        (name, password_hasher.hash(password), email, int(time.time()))
    )

def does_user_exist(cur: sqlite3.Cursor, name: str) -> bool:
    cur.execute("SELECT 1 FROM accounts WHERE name = ?", (name,))
    return cur.fetchone() is not None

def get_password_hash(cur: sqlite3.Cursor, name: str) -> Optional[str]:
    cur.execute("SELECT password_hash FROM accounts WHERE name = ?", (name,))
    fetch = cur.fetchone()
    if fetch is None:
        return None
    return fetch[0]

def verify_password(cur: sqlite3.Cursor, name: str, password: str) -> bool:
    password_hash = get_password_hash(cur, name)
    if password_hash is None:
        raise UserNotFoundError
    return password_hasher.verify(password_hash, password)