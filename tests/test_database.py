import sqlite3

import pytest

from database.db import (
    initialize_database,
    save_profile,
    load_profile,
    record_skill_progress,
    get_progress_history,
)


USER_PROFILE = {
    "skills": {
        "networking": 8,
        "linux": 7,
        "cloud": 3,
    },
    "interests": [
        "networking",
        "problem_solving",
    ],
    "completed_projects": 1,
}


def test_database_tables_are_created(tmp_path):
    db_path = tmp_path / "test.db"

    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = {
        row[0]
        for row in rows
    }

    assert "profiles" in table_names
    assert "progress" in table_names


def test_save_and_load_profile(tmp_path):
    db_path = tmp_path / "test.db"

    profile_id = save_profile(
        "demo_user",
        USER_PROFILE,
        db_path,
    )

    loaded_profile = load_profile(
        "demo_user",
        db_path,
    )

    assert profile_id > 0
    assert loaded_profile == USER_PROFILE


def test_existing_profile_is_updated(tmp_path):
    db_path = tmp_path / "test.db"

    save_profile(
        "demo_user",
        USER_PROFILE,
        db_path,
    )

    updated_profile = {
        **USER_PROFILE,
        "skills": {
            **USER_PROFILE["skills"],
            "networking": 9,
        },
    }

    first_id = save_profile(
        "demo_user",
        updated_profile,
        db_path,
    )

    loaded_profile = load_profile(
        "demo_user",
        db_path,
    )

    with sqlite3.connect(db_path) as connection:
        profile_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM profiles
            """
        ).fetchone()[0]

    assert first_id > 0
    assert profile_count == 1
    assert (
        loaded_profile["skills"]["networking"]
        == 9
    )


def test_missing_profile_returns_none(tmp_path):
    db_path = tmp_path / "test.db"

    result = load_profile(
        "missing_user",
        db_path,
    )

    assert result is None


def test_record_and_load_progress(tmp_path):
    db_path = tmp_path / "test.db"

    save_profile(
        "demo_user",
        USER_PROFILE,
        db_path,
    )

    progress_id = record_skill_progress(
        profile_name="demo_user",
        career_name="Network Engineer",
        skill="networking",
        old_level=8,
        new_level=9,
        db_path=db_path,
    )

    history = get_progress_history(
        "demo_user",
        db_path,
    )

    assert progress_id > 0
    assert len(history) == 1
    assert history[0]["skill"] == "networking"
    assert history[0]["old_level"] == 8
    assert history[0]["new_level"] == 9
    assert history[0]["improvement"] == 1
    assert history[0]["completed"] is True


def test_multiple_progress_entries(tmp_path):
    db_path = tmp_path / "test.db"

    save_profile(
        "demo_user",
        USER_PROFILE,
        db_path,
    )

    record_skill_progress(
        "demo_user",
        "Network Engineer",
        "networking",
        8,
        9,
        db_path,
    )

    record_skill_progress(
        "demo_user",
        "Network Engineer",
        "cloud",
        3,
        5,
        db_path,
    )

    history = get_progress_history(
        "demo_user",
        db_path,
    )

    assert len(history) == 2
    assert history[0]["skill"] == "networking"
    assert history[1]["skill"] == "cloud"


def test_unknown_profile_progress_is_invalid(
    tmp_path,
):
    db_path = tmp_path / "test.db"

    with pytest.raises(
        ValueError,
        match="Profile not found",
    ):
        record_skill_progress(
            "missing_user",
            "Network Engineer",
            "networking",
            8,
            9,
            db_path,
        )


def test_invalid_skill_level(tmp_path):
    db_path = tmp_path / "test.db"

    save_profile(
        "demo_user",
        USER_PROFILE,
        db_path,
    )

    with pytest.raises(ValueError):
        record_skill_progress(
            "demo_user",
            "Network Engineer",
            "networking",
            8,
            11,
            db_path,
        )