"""Tests for local and deployed database configuration."""

from database.db import (
    _normalize_database_url,
    get_default_database_target,
)


def test_local_path_becomes_sqlite_url(tmp_path):
    database_path = tmp_path / "careerforge.db"

    result = _normalize_database_url(database_path)

    assert result.startswith("sqlite+pysqlite:///")
    assert result.endswith("careerforge.db")


def test_neon_url_uses_psycopg2_driver():
    result = _normalize_database_url(
        "postgresql://user:password@example.com/neondb?sslmode=require"
    )

    assert result.startswith("postgresql+psycopg2://")
    assert result.endswith("neondb?sslmode=require")


def test_database_url_has_environment_priority(monkeypatch):
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        "/tmp/local-careerforge.db",
    )
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@example.com/neondb",
    )

    assert get_default_database_target().startswith("postgresql://")
