"""Database operations for CareerForge.

Local development and tests use SQLite. A deployed application can use a
PostgreSQL database by setting the ``DATABASE_URL`` environment variable.
"""

import json
import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy import (
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    insert,
    select,
    text,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool


DEFAULT_DATABASE_PATH = "careerforge.db"

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(30), nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("password_salt", Text, nullable=False),
    Column(
        "created_at",
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    UniqueConstraint("username", name="uq_users_username"),
)

profiles = Table(
    "profiles",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("profile_name", String(30), nullable=False),
    Column("profile_data", Text, nullable=False),
    Column(
        "created_at",
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    Column(
        "updated_at",
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    UniqueConstraint("profile_name", name="uq_profiles_profile_name"),
)

progress = Table(
    "progress",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "profile_id",
        Integer,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("career_name", Text, nullable=False),
    Column("skill", Text, nullable=False),
    Column("old_level", Integer, nullable=False),
    Column("new_level", Integer, nullable=False),
    Column("completed", Integer, nullable=False, server_default=text("1")),
    Column(
        "recorded_at",
        Text,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
)

Index("index_progress_profile_id", progress.c.profile_id)


def _validate_profile_name(profile_name):
    """Validate a profile name."""

    if not isinstance(profile_name, str) or not profile_name.strip():
        raise ValueError("profile_name must be a non-empty string")


def _validate_username(username):
    """Validate a database username value."""

    if not isinstance(username, str) or not username.strip():
        raise ValueError("username must be a non-empty string")


def _validate_skill_level(level, field_name):
    """Validate a skill level between 0 and 10."""

    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or not 0 <= level <= 10
    ):
        raise ValueError(
            f"{field_name} must be an integer between 0 and 10"
        )


def get_default_database_target():
    """Return the configured database URL or local SQLite path."""

    return (
        os.environ.get("DATABASE_URL")
        or os.environ.get("CAREERFORGE_DB_PATH")
        or DEFAULT_DATABASE_PATH
    )


def _normalize_database_url(database_target):
    """Convert a path or database URL into a SQLAlchemy URL."""

    if database_target is None:
        database_target = get_default_database_target()

    if isinstance(database_target, Path):
        database_target = str(database_target)

    if not isinstance(database_target, str) or not database_target.strip():
        raise ValueError("database target must be a path or database URL")

    target = database_target.strip()

    if target.startswith("postgres://"):
        return "postgresql+psycopg2://" + target[len("postgres://") :]

    if target.startswith("postgresql://"):
        return (
            "postgresql+psycopg2://"
            + target[len("postgresql://") :]
        )

    if target.startswith("postgresql+") or target.startswith("sqlite+"):
        return target

    if target.startswith("sqlite://"):
        return target.replace("sqlite://", "sqlite+pysqlite://", 1)

    if target == ":memory:":
        return "sqlite+pysqlite:///:memory:"

    database_path = Path(target).expanduser()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+pysqlite:///{database_path.resolve()}"


@lru_cache(maxsize=16)
def _engine_for_url(database_url):
    """Create and cache a SQLAlchemy engine."""

    options = {"pool_pre_ping": True}

    if database_url.startswith("sqlite+"):
        options["connect_args"] = {"check_same_thread": False}

        if database_url.endswith(":memory:"):
            options["poolclass"] = StaticPool

    return create_engine(database_url, **options)


def _get_engine(database_target=None):
    """Return the engine for a path or connection URL."""

    return _engine_for_url(_normalize_database_url(database_target))


def initialize_database(database_target=None):
    """Create the required database tables."""

    metadata.create_all(_get_engine(database_target))


def create_user(
    username,
    password_hash,
    password_salt,
    db_path=None,
):
    """Store a new user account and return its ID."""

    _validate_username(username)

    if not isinstance(password_hash, str) or not password_hash:
        raise ValueError("password_hash must be a non-empty string")

    if not isinstance(password_salt, str) or not password_salt:
        raise ValueError("password_salt must be a non-empty string")

    initialize_database(db_path)
    normalized_username = username.strip().lower()
    engine = _get_engine(db_path)

    try:
        with engine.begin() as connection:
            result = connection.execute(
                insert(users).values(
                    username=normalized_username,
                    password_hash=password_hash,
                    password_salt=password_salt,
                )
            )
            return result.inserted_primary_key[0]
    except IntegrityError as error:
        raise ValueError("username already exists") from error


def get_user_by_username(username, db_path=None):
    """Return a stored user account or None."""

    _validate_username(username)
    initialize_database(db_path)
    normalized_username = username.strip().lower()

    statement = select(
        users.c.id,
        users.c.username,
        users.c.password_hash,
        users.c.password_salt,
        users.c.created_at,
    ).where(users.c.username == normalized_username)

    with _get_engine(db_path).connect() as connection:
        row = connection.execute(statement).mappings().first()

    return dict(row) if row is not None else None


def save_profile(profile_name, user_profile, db_path=None):
    """Create or update a user profile."""

    _validate_profile_name(profile_name)

    if not isinstance(user_profile, dict):
        raise ValueError("user_profile must be a dictionary")

    initialize_database(db_path)
    normalized_name = profile_name.strip().lower()
    profile_json = json.dumps(
        user_profile,
        ensure_ascii=False,
        sort_keys=True,
    )
    engine = _get_engine(db_path)

    with engine.begin() as connection:
        profile_id = connection.execute(
            select(profiles.c.id).where(
                profiles.c.profile_name == normalized_name
            )
        ).scalar_one_or_none()

        if profile_id is not None:
            connection.execute(
                update(profiles)
                .where(profiles.c.id == profile_id)
                .values(
                    profile_data=profile_json,
                    updated_at=text("CURRENT_TIMESTAMP"),
                )
            )
            return profile_id

        result = connection.execute(
            insert(profiles).values(
                profile_name=normalized_name,
                profile_data=profile_json,
            )
        )
        return result.inserted_primary_key[0]


def load_profile(profile_name, db_path=None):
    """Load a user profile by name."""

    _validate_profile_name(profile_name)
    initialize_database(db_path)
    normalized_name = profile_name.strip().lower()

    statement = select(profiles.c.profile_data).where(
        profiles.c.profile_name == normalized_name
    )

    with _get_engine(db_path).connect() as connection:
        profile_json = connection.execute(statement).scalar_one_or_none()

    return json.loads(profile_json) if profile_json is not None else None


def record_skill_progress(
    profile_name,
    career_name,
    skill,
    old_level,
    new_level,
    db_path=None,
):
    """Record a completed skill improvement."""

    _validate_profile_name(profile_name)

    if not isinstance(career_name, str) or not career_name.strip():
        raise ValueError("career_name must be a non-empty string")

    if not isinstance(skill, str) or not skill.strip():
        raise ValueError("skill must be a non-empty string")

    _validate_skill_level(old_level, "old_level")
    _validate_skill_level(new_level, "new_level")

    if new_level < old_level:
        raise ValueError("new_level cannot be lower than old_level")

    initialize_database(db_path)
    normalized_name = profile_name.strip().lower()
    engine = _get_engine(db_path)

    with engine.begin() as connection:
        profile_id = connection.execute(
            select(profiles.c.id).where(
                profiles.c.profile_name == normalized_name
            )
        ).scalar_one_or_none()

        if profile_id is None:
            raise ValueError(f"Profile not found: {profile_name}")

        result = connection.execute(
            insert(progress).values(
                profile_id=profile_id,
                career_name=career_name.strip(),
                skill=skill.strip(),
                old_level=old_level,
                new_level=new_level,
                completed=1,
            )
        )
        return result.inserted_primary_key[0]


def get_progress_history(profile_name, db_path=None):
    """Return all recorded progress entries."""

    _validate_profile_name(profile_name)
    initialize_database(db_path)
    normalized_name = profile_name.strip().lower()

    statement = (
        select(
            progress.c.id,
            progress.c.career_name,
            progress.c.skill,
            progress.c.old_level,
            progress.c.new_level,
            progress.c.completed,
            progress.c.recorded_at,
        )
        .select_from(
            progress.join(
                profiles,
                profiles.c.id == progress.c.profile_id,
            )
        )
        .where(profiles.c.profile_name == normalized_name)
        .order_by(progress.c.id.asc())
    )

    with _get_engine(db_path).connect() as connection:
        rows = connection.execute(statement).mappings().all()

    return [
        {
            "id": row["id"],
            "career_name": row["career_name"],
            "skill": row["skill"],
            "old_level": row["old_level"],
            "new_level": row["new_level"],
            "improvement": row["new_level"] - row["old_level"],
            "completed": bool(row["completed"]),
            "recorded_at": row["recorded_at"],
        }
        for row in rows
    ]
