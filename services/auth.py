"""Authentication services for CareerForge."""

import hashlib
import hmac
import re
import secrets

from database.db import (
    create_user,
    get_user_by_username,
)


PBKDF2_ITERATIONS = 500_000
SALT_BYTES = 16
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")
INVALID_LOGIN_MESSAGE = "Invalid username or password."


def normalize_username(username):
    """Return the canonical lowercase username."""

    if not isinstance(username, str):
        return ""

    return username.strip().lower()


def validate_username(username):
    """Validate a username and return an error message or None."""

    normalized = normalize_username(username)

    if not USERNAME_PATTERN.fullmatch(normalized):
        return (
            "Username must be 3-30 characters and contain "
            "only letters, numbers, or underscores."
        )

    return None


def validate_password(password):
    """Validate a password and return an error message or None."""

    if not isinstance(password, str):
        return "Password must be a string."

    if len(password) < MIN_PASSWORD_LENGTH:
        return (
            f"Password must contain at least "
            f"{MIN_PASSWORD_LENGTH} characters."
        )

    if len(password) > MAX_PASSWORD_LENGTH:
        return (
            f"Password cannot exceed "
            f"{MAX_PASSWORD_LENGTH} characters."
        )

    if not password.strip():
        return "Password cannot contain only spaces."

    return None


def hash_password(password, salt=None):
    """Hash a password with PBKDF2-HMAC-SHA256."""

    password_error = validate_password(password)

    if password_error:
        raise ValueError(password_error)

    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)

    if not isinstance(salt, bytes) or len(salt) < SALT_BYTES:
        raise ValueError(
            "salt must contain at least 16 bytes"
        )

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return password_hash.hex(), salt.hex()


def verify_password(
    password,
    stored_hash,
    stored_salt,
):
    """Return whether a password matches a stored hash."""

    if not all(
        isinstance(value, str)
        for value in (
            password,
            stored_hash,
            stored_salt,
        )
    ):
        return False

    try:
        salt = bytes.fromhex(stored_salt)
        expected_hash = bytes.fromhex(stored_hash)
    except ValueError:
        return False

    candidate_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return hmac.compare_digest(
        candidate_hash,
        expected_hash,
    )


def register_user(
    username,
    password,
    confirm_password,
    db_path,
):
    """Validate and create a CareerForge user account."""

    normalized = normalize_username(username)
    username_error = validate_username(normalized)

    if username_error:
        return {
            "success": False,
            "message": username_error,
        }

    password_error = validate_password(password)

    if password_error:
        return {
            "success": False,
            "message": password_error,
        }

    if password != confirm_password:
        return {
            "success": False,
            "message": "Passwords do not match.",
        }

    if get_user_by_username(normalized, db_path) is not None:
        return {
            "success": False,
            "message": "Username already exists.",
        }

    password_hash, password_salt = hash_password(password)

    try:
        user_id = create_user(
            normalized,
            password_hash,
            password_salt,
            db_path,
        )
    except ValueError:
        return {
            "success": False,
            "message": "Username already exists.",
        }

    return {
        "success": True,
        "message": "Account created successfully.",
        "user": {
            "id": user_id,
            "username": normalized,
        },
    }


def login_user(username, password, db_path):
    """Authenticate a CareerForge user account."""

    normalized = normalize_username(username)

    if not normalized or not isinstance(password, str):
        return {
            "success": False,
            "message": INVALID_LOGIN_MESSAGE,
        }

    user = get_user_by_username(normalized, db_path)

    if user is None or not verify_password(
        password,
        user["password_hash"],
        user["password_salt"],
    ):
        return {
            "success": False,
            "message": INVALID_LOGIN_MESSAGE,
        }

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
        },
    }