import pytest

from services.what_if import simulate_skill_change


TEST_PROFILE = {
    "skills": {
        "python": 6,
        "linux": 7,
        "networking": 8,
        "cybersecurity": 7,
        "siem": 3,
        "incident_response": 2,
        "routing_switching": 6,
        "network_security": 6,
        "cloud": 3,
        "aws": 2,
        "docker": 3,
        "sql": 4,
        "statistics": 3,
        "data_visualization": 2,
        "excel": 5,
        "web_development": 3,
        "apis": 2,
        "databases": 4
    },
    "interests": [
        "cybersecurity",
        "networking",
        "problem_solving"
    ]
}


def find_career_change(result, career_id):
    return next(
        change
        for change in result["career_changes"]
        if change["id"] == career_id
    )


def test_cloud_improvement_increases_cloud_score():
    original_cloud_level = TEST_PROFILE[
        "skills"
    ]["cloud"]

    result = simulate_skill_change(
        TEST_PROFILE,
        skill="cloud",
        new_level=8
    )

    cloud_change = find_career_change(
        result,
        "cloud_engineer"
    )

    assert (
        cloud_change["after_score"]
        > cloud_change["before_score"]
    )

    assert cloud_change["score_change"] > 0

    # Original profile must remain unchanged.
    assert (
        TEST_PROFILE["skills"]["cloud"]
        == original_cloud_level
    )


def test_after_recommendations_are_sorted():
    result = simulate_skill_change(
        TEST_PROFILE,
        skill="cloud",
        new_level=8
    )

    scores = [
        career["final_score"]
        for career in result[
            "after_recommendations"
        ]
    ]

    assert scores == sorted(
        scores,
        reverse=True
    )


def test_same_level_produces_no_change():
    result = simulate_skill_change(
        TEST_PROFILE,
        skill="cloud",
        new_level=3
    )

    assert all(
        change["score_change"] == 0
        for change in result["career_changes"]
    )

    assert result["biggest_improvement"] is None


def test_invalid_skill_level():
    with pytest.raises(ValueError):
        simulate_skill_change(
            TEST_PROFILE,
            skill="cloud",
            new_level=11
        )


def test_empty_skill_name():
    with pytest.raises(ValueError):
        simulate_skill_change(
            TEST_PROFILE,
            skill="",
            new_level=5
        )