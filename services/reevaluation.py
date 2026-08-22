"""Dynamically re-evaluate career progress."""

from services.recommendation import recommend_careers
from services.skill_gap import analyze_skill_gap
from services.readiness import calculate_readiness


def _find_career(recommendations, career_name):
    """Find a career result by name."""

    for career in recommendations:
        if career["name"] == career_name:
            return career

    raise ValueError(
        f"Career not found: {career_name}"
    )


def _find_rank(recommendations, career_name):
    """Return the career's ranking position."""

    for position, career in enumerate(
        recommendations,
        start=1,
    ):
        if career["name"] == career_name:
            return position

    raise ValueError(
        f"Career not found: {career_name}"
    )


def _calculate_total_gap(gap_result):
    """Return the combined skill-gap value."""

    return sum(
        item["gap"]
        for item in gap_result["skill_details"]
    )


def _calculate_career_readiness(
    user_profile,
    career,
    gap_result,
):
    """Calculate readiness for one career."""

    return calculate_readiness(
        technical_score=career["weighted_score"],
        completion_score=gap_result[
            "completion_percentage"
        ],
        interest_score=career["interest_score"],
        completed_projects=user_profile.get(
            "completed_projects",
            0,
        ),
        target_projects=career.get(
            "target_projects",
            2,
        ),
    )


def reevaluate_profile(
    original_profile,
    updated_profile,
    career_name,
    limit=100,
):
    """
    Compare career results before and after
    updating a user profile.
    """

    if not isinstance(original_profile, dict):
        raise ValueError(
            "original_profile must be a dictionary"
        )

    if not isinstance(updated_profile, dict):
        raise ValueError(
            "updated_profile must be a dictionary"
        )

    if (
        not isinstance(career_name, str)
        or not career_name.strip()
    ):
        raise ValueError(
            "career_name must be a non-empty string"
        )

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit <= 0
    ):
        raise ValueError(
            "limit must be a positive integer"
        )

    before_recommendations = recommend_careers(
        original_profile,
        limit=limit,
    )

    after_recommendations = recommend_careers(
        updated_profile,
        limit=limit,
    )

    before_career = _find_career(
        before_recommendations,
        career_name,
    )

    after_career = _find_career(
        after_recommendations,
        career_name,
    )

    before_rank = _find_rank(
        before_recommendations,
        career_name,
    )

    after_rank = _find_rank(
        after_recommendations,
        career_name,
    )

    before_gap = analyze_skill_gap(
        original_profile.get("skills", {}),
        before_career["required_skills"],
    )

    after_gap = analyze_skill_gap(
        updated_profile.get("skills", {}),
        after_career["required_skills"],
    )

    before_readiness = _calculate_career_readiness(
        original_profile,
        before_career,
        before_gap,
    )

    after_readiness = _calculate_career_readiness(
        updated_profile,
        after_career,
        after_gap,
    )

    before_total_gap = _calculate_total_gap(
        before_gap
    )

    after_total_gap = _calculate_total_gap(
        after_gap
    )

    return {
        "career_name": career_name,
        "before": {
            "rank": before_rank,
            "recommendation": before_career,
            "skill_gap": before_gap,
            "total_gap": before_total_gap,
            "readiness": before_readiness,
        },
        "after": {
            "rank": after_rank,
            "recommendation": after_career,
            "skill_gap": after_gap,
            "total_gap": after_total_gap,
            "readiness": after_readiness,
        },
        "changes": {
            "career_score": round(
                after_career["final_score"]
                - before_career["final_score"],
                2,
            ),
            "rank_improvement": (
                before_rank - after_rank
            ),
            "readiness": round(
                after_readiness["overall_score"]
                - before_readiness["overall_score"],
                2,
            ),
            "completion": round(
                after_gap["completion_percentage"]
                - before_gap[
                    "completion_percentage"
                ],
                2,
            ),
            "gap_reduction": (
                before_total_gap
                - after_total_gap
            ),
        },
        "updated_recommendations": (
            after_recommendations
        ),
    }