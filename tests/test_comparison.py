import pytest

from services.comparison import compare_careers


MOCK_RECOMMENDATIONS = [
    {
        "name": "Network Engineer",
        "category": "Network and Systems",
        "final_score": 85.03,
        "cosine_score": 96.75,
        "weighted_score": 82.50,
        "interest_score": 66.67,
    },
    {
        "name": "SOC Analyst",
        "category": "Cybersecurity",
        "final_score": 84.22,
        "cosine_score": 89.44,
        "weighted_score": 71.11,
        "interest_score": 100.00,
    },
]


@pytest.fixture
def mock_recommendations(monkeypatch):
    def fake_recommend_careers(
        user_profile,
        limit=5,
    ):
        return MOCK_RECOMMENDATIONS[:limit]

    monkeypatch.setattr(
        "services.comparison.recommend_careers",
        fake_recommend_careers,
    )


def test_overall_winner(mock_recommendations):
    result = compare_careers(
        {},
        "Network Engineer",
        "SOC Analyst",
    )

    assert result["overall_winner"] == "Network Engineer"
    assert result["score_difference"] == 0.81


def test_component_winners(mock_recommendations):
    result = compare_careers(
        {},
        "Network Engineer",
        "SOC Analyst",
    )

    winners = result["metric_winners"]

    assert (
        winners["cosine_similarity"]
        == "Network Engineer"
    )

    assert (
        winners["weighted_score"]
        == "Network Engineer"
    )

    assert winners["interest_match"] == "SOC Analyst"


def test_comparison_contains_both_careers(
    mock_recommendations,
):
    result = compare_careers(
        {},
        "Network Engineer",
        "SOC Analyst",
    )

    assert (
        result["career_a"]["name"]
        == "Network Engineer"
    )

    assert (
        result["career_b"]["name"]
        == "SOC Analyst"
    )


def test_same_career_is_invalid(mock_recommendations):
    with pytest.raises(ValueError):
        compare_careers(
            {},
            "SOC Analyst",
            "SOC Analyst",
        )


def test_unknown_career_is_invalid(
    mock_recommendations,
):
    with pytest.raises(
        ValueError,
        match="Career not found",
    ):
        compare_careers(
            {},
            "Network Engineer",
            "Unknown Career",
        )