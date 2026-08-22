from numbers import Real


def calculate_weighted_score(
    user_skills,
    required_skills,
    skill_weights=None
):
    """
    Calculate how well the user's skill levels satisfy
    a career's required skill levels.

    Returns a percentage between 0 and 100.
    """

    if not isinstance(user_skills, dict):
        raise TypeError("user_skills must be a dictionary.")

    if not isinstance(required_skills, dict):
        raise TypeError("required_skills must be a dictionary.")

    if not required_skills:
        return 0.0

    if skill_weights is not None and not isinstance(skill_weights, dict):
        raise TypeError("skill_weights must be a dictionary.")

    weighted_score = 0.0
    total_weight = 0.0

    for skill, required_level in required_skills.items():
        user_level = user_skills.get(skill, 0)

        if not isinstance(required_level, Real):
            raise TypeError(f"Required level for {skill} must be numeric.")

        if not isinstance(user_level, Real):
            raise TypeError(f"User level for {skill} must be numeric.")

        if not 1 <= required_level <= 10:
            raise ValueError(
                f"Required level for {skill} must be between 1 and 10."
            )

        if not 0 <= user_level <= 10:
            raise ValueError(
                f"User level for {skill} must be between 0 and 10."
            )

        if skill_weights is None:
            weight = required_level
        else:
            weight = skill_weights.get(skill, required_level)

        if not isinstance(weight, Real) or weight <= 0:
            raise ValueError(
                f"Weight for {skill} must be a positive number."
            )

        achievement_ratio = min(
            user_level / required_level,
            1.0
        )

        weighted_score += achievement_ratio * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(
        (weighted_score / total_weight) * 100,
        2
    )