import pytest

from services.recommendation import (
    calculate_interest_match,
    recommend_careers,
)


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


def test_interest_matching():
    result = calculate_interest_match(
        ["Cybersecurity", "Problem Solving"],
        ["cybersecurity", "problem_solving", "networking"]
    )

    assert result == 66.67


def test_recommendation_limit_and_sorting():
    results = recommend_careers(
        TEST_PROFILE,
        limit=3
    )

    assert len(results) == 3

    scores = [
        career["final_score"]
        for career in results
    ]

    assert scores == sorted(scores, reverse=True)


def test_recommendation_result_fields():
    result = recommend_careers(
        TEST_PROFILE,
        limit=1
    )[0]

    expected_fields = {
        "id",
        "name",
        "category",
        "description",
        "required_skills",
        "cosine_score",
        "weighted_score",
        "interest_score",
        "final_score"
    }

    assert expected_fields.issubset(result.keys())


def test_invalid_recommendation_limit():
    with pytest.raises(ValueError):
        recommend_careers(
            TEST_PROFILE,
            limit=0
        )