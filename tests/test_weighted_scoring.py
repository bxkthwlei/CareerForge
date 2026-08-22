import pytest

from algorithms.weighted_scoring import calculate_weighted_score


def test_full_skill_match():
    user_skills = {
        "python": 8,
        "sql": 7
    }

    required_skills = {
        "python": 8,
        "sql": 7
    }

    result = calculate_weighted_score(
        user_skills,
        required_skills
    )

    assert result == 100.0


def test_partial_skill_match():
    user_skills = {
        "networking": 8,
        "linux": 7,
        "cybersecurity": 6,
        "siem": 3,
        "incident_response": 2,
        "python": 6
    }

    required_skills = {
        "networking": 8,
        "linux": 7,
        "cybersecurity": 8,
        "siem": 9,
        "incident_response": 8,
        "python": 5
    }

    result = calculate_weighted_score(
        user_skills,
        required_skills
    )

    assert result == 68.89


def test_missing_skill_counts_as_zero():
    user_skills = {
        "python": 5
    }

    required_skills = {
        "python": 5,
        "sql": 5
    }

    result = calculate_weighted_score(
        user_skills,
        required_skills
    )

    assert result == 50.0


def test_custom_skill_weights():
    user_skills = {
        "python": 5,
        "sql": 0
    }

    required_skills = {
        "python": 5,
        "sql": 5
    }

    skill_weights = {
        "python": 2,
        "sql": 8
    }

    result = calculate_weighted_score(
        user_skills,
        required_skills,
        skill_weights
    )

    assert result == 20.0


def test_empty_requirements():
    result = calculate_weighted_score(
        {"python": 5},
        {}
    )

    assert result == 0.0


def test_invalid_skill_level():
    with pytest.raises(ValueError):
        calculate_weighted_score(
            {"python": 11},
            {"python": 8}
        )