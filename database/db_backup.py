"""SQLite database operations for CareerForge."""

import json
import sqlite3
from pathlib import Path


DEFAULT_DATABASE_PATH = "careerforge.db"


def _validate_profile_name(profile_name):
    """Validate a profile name."""

    if (
        not isinstance(profile_name, str)
        or not profile_name.strip()
    ):
        raise ValueError(
            "profile_name must be a non-empty string"
        )


def _validate_skill_level(level, field_name):
    """Validate a skill level between 0 and 10."""

    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or not 0 <= level <= 10
    ):
        raise ValueError(
            f"{field_name} must be an integer "
            "between 0 and 10"
        )


def _connect(db_path):
    """Create a configured SQLite connection."""

    database_path = Path(db_path)

    if database_path.parent != Path("."):
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    connection = sqlite3.connect(
        database_path
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def initialize_database(
    db_path=DEFAULT_DATABASE_PATH,
):
    """Create the required database tables."""

    with _connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT NOT NULL UNIQUE,
                profile_data TEXT NOT NULL,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                career_name TEXT NOT NULL,
                skill TEXT NOT NULL,
                old_level INTEGER NOT NULL,
                new_level INTEGER NOT NULL,
                completed INTEGER NOT NULL DEFAULT 1,
                recorded_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (profile_id)
                    REFERENCES profiles(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS
                index_progress_profile_id
            ON progress(profile_id);
            """
        )


def save_profile(
    profile_name,
    user_profile,
    db_path=DEFAULT_DATABASE_PATH,
):
    """Create or update a user profile."""

    _validate_profile_name(profile_name)

    if not isinstance(user_profile, dict):
        raise ValueError(
            "user_profile must be a dictionary"
        )

    initialize_database(db_path)

    profile_json = json.dumps(
        user_profile,
        ensure_ascii=False,
        sort_keys=True,
    )

    with _connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO profiles (
                profile_name,
                profile_data
            )
            VALUES (?, ?)

            ON CONFLICT(profile_name)
            DO UPDATE SET
                profile_data = excluded.profile_data,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                profile_name.strip(),
                profile_json,
            ),
        )

        row = connection.execute(
            """
            SELECT id
            FROM profiles
            WHERE profile_name = ?
            """,
            (profile_name.strip(),),
        ).fetchone()

    return row["id"]


def load_profile(
    profile_name,
    db_path=DEFAULT_DATABASE_PATH,
):
    """Load a user profile by name."""

    _validate_profile_name(profile_name)
    initialize_database(db_path)

    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT profile_data
            FROM profiles
            WHERE profile_name = ?
            """,
            (profile_name.strip(),),
        ).fetchone()

    if row is None:
        return None

    return json.loads(row["profile_data"])


def record_skill_progress(
    profile_name,
    career_name,
    skill,
    old_level,
    new_level,
    db_path=DEFAULT_DATABASE_PATH,
):
    """Record a completed skill improvement."""

    _validate_profile_name(profile_name)

    if (
        not isinstance(career_name, str)
        or not career_name.strip()
    ):
        raise ValueError(
            "career_name must be a non-empty string"
        )

    if (
        not isinstance(skill, str)
        or not skill.strip()
    ):
        raise ValueError(
            "skill must be a non-empty string"
        )

    _validate_skill_level(
        old_level,
        "old_level",
    )

    _validate_skill_level(
        new_level,
        "new_level",
    )

    if new_level < old_level:
        raise ValueError(
            "new_level cannot be lower "
            "than old_level"
        )

    initialize_database(db_path)

    with _connect(db_path) as connection:
        profile_row = connection.execute(
            """
            SELECT id
            FROM profiles
            WHERE profile_name = ?
            """,
            (profile_name.strip(),),
        ).fetchone()

        if profile_row is None:
            raise ValueError(
                f"Profile not found: "
                f"{profile_name}"
            )

        cursor = connection.execute(
            """
            INSERT INTO progress (
                profile_id,
                career_name,
                skill,
                old_level,
                new_level,
                completed
            )
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (
                profile_row["id"],
                career_name.strip(),
                skill.strip(),
                old_level,
                new_level,
            ),
        )

        progress_id = cursor.lastrowid

    return progress_id


def get_progress_history(
    profile_name,
    db_path=DEFAULT_DATABASE_PATH,
):
    """Return all recorded progress entries."""

    _validate_profile_name(profile_name)
    initialize_database(db_path)

    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                progress.id,
                progress.career_name,
                progress.skill,
                progress.old_level,
                progress.new_level,
                progress.completed,
                progress.recorded_at
            FROM progress
            JOIN profiles
                ON profiles.id = progress.profile_id
            WHERE profiles.profile_name = ?
            ORDER BY progress.id ASC
            """,
            (profile_name.strip(),),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "career_name": row["career_name"],
            "skill": row["skill"],
            "old_level": row["old_level"],
            "new_level": row["new_level"],
            "improvement": (
                row["new_level"]
                - row["old_level"]
            ),
            "completed": bool(
                row["completed"]
            ),
            "recorded_at": row[
                "recorded_at"
            ],
        }
        for row in rows
    ]