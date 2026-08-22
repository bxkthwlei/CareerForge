from copy import deepcopy
from numbers import Real

from services.recommendation import (
    load_careers,
    recommend_careers
)


def simulate_skill_change(
    user_profile,
    skill,
    new_level,
    limit=5
):
    """
    Simulate a skill-level change without modifying
    the original user profile.

    Returns before/after recommendations and
    career-score changes.
    """

    if not isinstance(user_profile, dict):
        raise TypeError(
            "user_profile must be a dictionary."
        )

    if not isinstance(skill, str) or not skill.strip():
        raise ValueError(
            "skill must be a non-empty string."
        )

    if not isinstance(new_level, Real):
        raise TypeError(
            "new_level must be numeric."
        )

    if not 0 <= new_level <= 10:
        raise ValueError(
            "new_level must be between 0 and 10."
        )

    if not isinstance(limit, int) or limit <= 0:
        raise ValueError(
            "limit must be a positive integer."
        )

    if not isinstance(
        user_profile.get("skills", {}),
        dict
    ):
        raise TypeError(
            "User skills must be a dictionary."
        )

    normalized_skill = (
        skill.strip()
        .lower()
        .replace(" ", "_")
    )

    original_profile = deepcopy(user_profile)
    simulated_profile = deepcopy(user_profile)

    old_level = original_profile.get(
        "skills",
        {}
    ).get(normalized_skill, 0)

    simulated_profile.setdefault(
        "skills",
        {}
    )[normalized_skill] = new_level

    career_count = len(load_careers())

    before_results = recommend_careers(
        original_profile,
        limit=career_count
    )

    after_results = recommend_careers(
        simulated_profile,
        limit=career_count
    )

    before_by_id = {
        career["id"]: career
        for career in before_results
    }

    before_ranks = {
        career["id"]: rank
        for rank, career in enumerate(
            before_results,
            start=1
        )
    }

    after_ranks = {
        career["id"]: rank
        for rank, career in enumerate(
            after_results,
            start=1
        )
    }

    career_changes = []

    for career in after_results:
        career_id = career["id"]
        before_career = before_by_id[career_id]

        before_score = before_career["final_score"]
        after_score = career["final_score"]

        score_change = round(
            after_score - before_score,
            2
        )

        rank_change = (
            before_ranks[career_id]
            - after_ranks[career_id]
        )

        career_changes.append({
            "id": career_id,
            "name": career["name"],
            "before_score": before_score,
            "after_score": after_score,
            "score_change": score_change,
            "before_rank": before_ranks[career_id],
            "after_rank": after_ranks[career_id],
            "rank_change": rank_change
        })

    career_changes.sort(
        key=lambda item: (
            item["score_change"],
            item["after_score"]
        ),
        reverse=True
    )

    positive_changes = [
        change
        for change in career_changes
        if change["score_change"] > 0
    ]

    biggest_improvement = (
        positive_changes[0]
        if positive_changes
        else None
    )

    return {
        "skill": normalized_skill,
        "old_level": old_level,
        "new_level": new_level,
        "before_recommendations": before_results[
            :limit
        ],
        "after_recommendations": after_results[
            :limit
        ],
        "career_changes": career_changes,
        "biggest_improvement": biggest_improvement
    }