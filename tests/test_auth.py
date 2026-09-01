"""Tests for CareerForge authentication."""

from database.db import (
    get_user_by_username,
    initialize_database,
)
from services.auth import (
    INVALID_LOGIN_MESSAGE,
    login_user,
    register_user,
    verify_password,
)


VALID_PASSWORD = "CareerForge123!"


def test_initialize_database_creates_users_table(tmp_path):
    database_path = tmp_path / "careerforge.db"

    initialize_database(database_path)

    assert get_user_by_username(
        "missing_user",
        database_path,
    ) is None


def test_register_and_login_user(tmp_path):
    database_path = tmp_path / "careerforge.db"

    registration = register_user(
        "Alice_01",
        "alice@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    login = login_user(
        "ALICE_01",
        VALID_PASSWORD,
        database_path,
    )

    assert registration["success"] is True
    assert registration["user"]["username"] == "alice_01"
    assert registration["user"]["email"] == "alice@example.com"
    assert login["success"] is True
    assert login["user"]["username"] == "alice_01"


def test_duplicate_username_is_rejected(tmp_path):
    database_path = tmp_path / "careerforge.db"

    first = register_user(
        "career_user",
        "career@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    duplicate = register_user(
        "CAREER_USER",
        "another@example.com",
        "AnotherPassword123!",
        "AnotherPassword123!",
        database_path,
    )

    assert first["success"] is True
    assert duplicate == {
        "success": False,
        "message": "Username already exists.",
    }


def test_duplicate_email_is_rejected_and_email_login_works(tmp_path):
    database_path = tmp_path / "careerforge.db"

    first = register_user(
        "email_user",
        "User@Example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    duplicate = register_user(
        "different_user",
        "user@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    login = login_user(
        "USER@example.com",
        VALID_PASSWORD,
        database_path,
    )

    assert first["success"] is True
    assert duplicate == {
        "success": False,
        "message": "Email already exists.",
    }
    assert login["success"] is True
    assert login["user"]["username"] == "email_user"


def test_invalid_email_is_rejected(tmp_path):
    result = register_user(
        "email_user",
        "not-an-email",
        VALID_PASSWORD,
        VALID_PASSWORD,
        tmp_path / "careerforge.db",
    )

    assert result == {
        "success": False,
        "message": "Enter a valid email address.",
    }


def test_wrong_password_and_unknown_user_are_rejected(tmp_path):
    database_path = tmp_path / "careerforge.db"

    register_user(
        "student",
        "student@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )

    wrong_password = login_user(
        "student",
        "WrongPassword123!",
        database_path,
    )
    unknown_user = login_user(
        "unknown",
        VALID_PASSWORD,
        database_path,
    )

    assert wrong_password == {
        "success": False,
        "message": INVALID_LOGIN_MESSAGE,
    }
    assert unknown_user == wrong_password


def test_registration_validates_input(tmp_path):
    database_path = tmp_path / "careerforge.db"

    invalid_username = register_user(
        "a!",
        "invalid@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    weak_password = register_user(
        "valid_user",
        "weak@example.com",
        "short",
        "short",
        database_path,
    )
    mismatch = register_user(
        "valid_user",
        "mismatch@example.com",
        VALID_PASSWORD,
        "DifferentPassword123!",
        database_path,
    )

    assert invalid_username["success"] is False
    assert weak_password["success"] is False
    assert mismatch == {
        "success": False,
        "message": "Passwords do not match.",
    }


def test_password_is_salted_and_not_stored_as_plaintext(tmp_path):
    database_path = tmp_path / "careerforge.db"

    register_user(
        "user_one",
        "one@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )
    register_user(
        "user_two",
        "two@example.com",
        VALID_PASSWORD,
        VALID_PASSWORD,
        database_path,
    )

    first = get_user_by_username(
        "user_one",
        database_path,
    )
    second = get_user_by_username(
        "user_two",
        database_path,
    )

    assert first["password_hash"] != VALID_PASSWORD
    assert first["password_hash"] != second["password_hash"]
    assert first["password_salt"] != second["password_salt"]
    assert verify_password(
        VALID_PASSWORD,
        first["password_hash"],
        first["password_salt"],
    ) is True


def test_malformed_stored_credentials_fail_safely():
    assert verify_password(
        VALID_PASSWORD,
        "not-hex",
        "not-hex",
    ) is False
