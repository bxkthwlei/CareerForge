"""Integration tests for the CareerForge Streamlit dashboard."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from services.auth import register_user


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "ui" / "app.py"
TEST_PASSWORD = "CareerForge123!"


def find_by_label(elements, label):
    """Return the first AppTest element with a matching label."""

    return next(
        element
        for element in elements
        if element.label == label
    )


def create_app():
    """Create and run an unauthenticated AppTest instance."""

    app = AppTest.from_file(
        str(APP_PATH),
        default_timeout=30,
    )
    app.run(timeout=30)
    return app


@pytest.fixture
def authenticated_app(tmp_path, monkeypatch):
    """Create an account and log in through the Streamlit UI."""

    database_path = tmp_path / "careerforge.db"
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        str(database_path),
    )
    registration = register_user(
        "test_user",
        TEST_PASSWORD,
        TEST_PASSWORD,
        database_path,
    )
    assert registration["success"] is True

    app = create_app()
    find_by_label(
        app.button,
        "Sign In",
    ).click().run(timeout=30)
    find_by_label(
        app.text_input,
        "Username",
    ).set_value("test_user")
    find_by_label(
        app.text_input,
        "Password",
    ).set_value(TEST_PASSWORD)
    find_by_label(
        app.button,
        "Login",
    ).click().run(timeout=30)

    assert not app.exception
    return app


def return_to_dashboard(app):
    """Navigate an authenticated test app to its dashboard."""

    button_labels = {
        item.label
        for item in app.button
    }

    if "← Dashboard" in button_labels:
        find_by_label(
            app.button,
            "← Dashboard",
        ).click().run(timeout=30)
        assert not app.exception


def test_landing_screen_is_initial_page(tmp_path, monkeypatch):
    database_path = tmp_path / "careerforge.db"
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        str(database_path),
    )

    app = create_app()

    assert not app.exception
    button_labels = {
        item.label
        for item in app.button
    }

    assert {
        "Start My Career Plan",
        "Sign In",
    }.issubset(
        button_labels
    )


def test_sign_in_opens_login_screen(tmp_path, monkeypatch):
    database_path = tmp_path / "careerforge.db"
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        str(database_path),
    )

    app = create_app()
    find_by_label(app.button, "Sign In").click().run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "CareerForge"
    assert app.subheader[0].value == "Login"

    input_labels = {item.label for item in app.text_input}
    assert {"Username", "Password"}.issubset(input_labels)
    assert "← Back to Home" in {
        item.label
        for item in app.button
    }


def test_login_can_return_to_landing_page(tmp_path, monkeypatch):
    """Allow an unauthenticated user to return home from login."""

    database_path = tmp_path / "careerforge.db"
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        str(database_path),
    )

    app = create_app()
    find_by_label(app.button, "Sign In").click().run(timeout=30)
    find_by_label(
        app.button,
        "← Back to Home",
    ).click().run(timeout=30)

    assert not app.exception
    assert "Start My Career Plan" in {
        item.label
        for item in app.button
    }


def test_register_screen_renders(tmp_path, monkeypatch):
    database_path = tmp_path / "careerforge.db"
    monkeypatch.setenv(
        "CAREERFORGE_DB_PATH",
        str(database_path),
    )

    app = create_app()
    find_by_label(
        app.button,
        "Start My Career Plan",
    ).click().run(timeout=30)

    assert not app.exception
    assert app.subheader[0].value == "Register"

    input_labels = {
        item.label
        for item in app.text_input
    }
    assert {
        "Username",
        "Password",
        "Confirm password",
    }.issubset(input_labels)


def test_landing_page_uses_full_width_layout():
    """Keep the public landing page wide without changing app pages."""

    source = APP_PATH.read_text(encoding="utf-8")

    assert ".block-container {" in source
    assert "max-width: none;" in source
    assert "width: 100%;" in source
    assert "apply_landing_styles()\n            render_landing_page()" in source


def test_non_landing_background_assets_exist():
    """Provide a dedicated optimized background for every app page."""

    background_directory = PROJECT_ROOT / "assets" / "backgrounds"
    expected_files = {
        "login.webp",
        "register.webp",
        "dashboard.webp",
        "overview.webp",
        "skill-gap.webp",
        "learning-roadmap.webp",
        "what-if.webp",
        "comparison.webp",
        "progress.webp",
    }

    assert expected_files == {
        path.name
        for path in background_directory.glob("*.webp")
    }
    assert all(
        (background_directory / name).stat().st_size > 0
        for name in expected_files
    )


def test_authenticated_dashboard_has_six_cards(
    authenticated_app,
):
    app = authenticated_app

    expected_buttons = {
        "Open Overview",
        "Open Skill Gap",
        "Open Learning & Roadmap",
        "Open What-If Simulator",
        "Open Career Comparison",
        "Open Progress Tracking",
    }
    button_labels = {
        item.label
        for item in app.button
    }

    assert expected_buttons.issubset(button_labels)


def test_profile_editor_controls_render(authenticated_app):
    app = authenticated_app

    assert app.multiselect
    assert app.slider

    button_labels = {
        item.label
        for item in app.button
    }
    assert "Save and Recalculate" in button_labels


@pytest.mark.parametrize(
    ("button_label", "expected_heading"),
    [
        ("Open Overview", "Top Career Matches"),
        ("Open Skill Gap", "Career Readiness"),
        ("Open Learning & Roadmap", "AI Learning Path"),
        ("Open What-If Simulator", "What-If Simulator"),
        ("Open Career Comparison", "Career Comparison"),
        ("Open Progress Tracking", "Progress Tracking"),
    ],
)
def test_feature_card_opens_separate_screen(
    authenticated_app,
    button_label,
    expected_heading,
):
    app = authenticated_app
    return_to_dashboard(app)

    find_by_label(
        app.button,
        button_label,
    ).click().run(timeout=30)

    assert not app.exception
    assert expected_heading in {
        item.value
        for item in app.subheader
    }
    assert "← Dashboard" in {
        item.label
        for item in app.button
    }


def test_logout_returns_to_landing_page(authenticated_app):
    app = authenticated_app

    find_by_label(
        app.button,
        "Logout",
    ).click().run(timeout=30)

    assert not app.exception
    assert "Sign In" in {
        item.label
        for item in app.button
    }
