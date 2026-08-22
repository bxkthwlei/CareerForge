"""Compare two career recommendation results."""

from services.recommendation import recommend_careers


def _get_metric_value(result, metric):
    """Return a recommendation metric value."""

    aliases = {
        "score": ("final_score", "score"),
        "cosine_similarity": (
            "cosine_score",
            "cosine_similarity",
        ),
        "weighted_score": ("weighted_score",),
        "interest_match": (
            "interest_score",
            "interest_match",
        ),
    }

    for key in aliases[metric]:
        if key in result:
            return result[key]

    return 0


def _metric_winner(career_a, career_b, metric):
    """Return the career with the higher metric."""

    value_a = _get_metric_value(career_a, metric)
    value_b = _get_metric_value(career_b, metric)

    if value_a > value_b:
        return career_a["name"]

    if value_b > value_a:
        return career_b["name"]

    return "Tie"


def compare_careers(
    user_profile,
    first_career,
    second_career,
):
    """Compare two careers using recommendation results."""

    if not isinstance(first_career, str) or not first_career.strip():
        raise ValueError(
            "first_career must be a non-empty string"
        )

    if not isinstance(second_career, str) or not second_career.strip():
        raise ValueError(
            "second_career must be a non-empty string"
        )

    if first_career == second_career:
        raise ValueError(
            "Two different careers are required"
        )

    # Use a large limit so careers outside the top five
    # can also be selected for comparison.
    recommendations = recommend_careers(
        user_profile,
        limit=100,
    )

    recommendations_by_name = {
        result["name"]: result
        for result in recommendations
    }

    missing_careers = [
        career_name
        for career_name in (
            first_career,
            second_career,
        )
        if career_name not in recommendations_by_name
    ]

    if missing_careers:
        missing_names = ", ".join(missing_careers)

        raise ValueError(
            f"Career not found: {missing_names}"
        )

    career_a = recommendations_by_name[first_career]
    career_b = recommendations_by_name[second_career]

    score_a = _get_metric_value(career_a, "score")
    score_b = _get_metric_value(career_b, "score")

    return {
        "career_a": career_a,
        "career_b": career_b,
        "overall_winner": _metric_winner(
            career_a,
            career_b,
            "score",
        ),
        "score_difference": round(
            abs(score_a - score_b),
            2,
        ),
        "metric_winners": {
            "cosine_similarity": _metric_winner(
                career_a,
                career_b,
                "cosine_similarity",
            ),
            "weighted_score": _metric_winner(
                career_a,
                career_b,
                "weighted_score",
            ),
            "interest_match": _metric_winner(
                career_a,
                career_b,
                "interest_match",
            ),
        },
    }