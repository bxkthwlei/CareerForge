"""Track user skill and learning-path progress."""

from copy import deepcopy


def update_skill_progress(
    user_profile,
    skill,
    new_level,
):
    """
    Update a skill level without modifying
    the original user profile.
    """

    if not isinstance(user_profile, dict):
        raise ValueError(
            "user_profile must be a dictionary"
        )

    if not isinstance(skill, str) or not skill.strip():
        raise ValueError(
            "skill must be a non-empty string"
        )

    if (
        not isinstance(new_level, int)
        or isinstance(new_level, bool)
        or not 0 <= new_level <= 10
    ):
        raise ValueError(
            "new_level must be an integer "
            "between 0 and 10"
        )

    current_level = (
        user_profile
        .get("skills", {})
        .get(skill, 0)
    )

    if new_level < current_level:
        raise ValueError(
            "new_level cannot be lower "
            "than the current level"
        )

    updated_profile = deepcopy(user_profile)

    updated_profile.setdefault(
        "skills",
        {},
    )

    updated_profile["skills"][skill] = new_level

    return {
        "skill": skill,
        "old_level": current_level,
        "new_level": new_level,
        "improvement": new_level - current_level,
        "updated_profile": updated_profile,
    }


def calculate_learning_progress(
    learning_path,
    completed_skills,
):
    """Calculate learning-path completion progress."""

    if isinstance(learning_path, dict):
        steps = learning_path.get(
            "learning_path",
            [],
        )
    elif isinstance(learning_path, list):
        steps = learning_path
    else:
        raise ValueError(
            "learning_path must be a dictionary "
            "or list"
        )

    if not isinstance(completed_skills, list):
        raise ValueError(
            "completed_skills must be a list"
        )

    path_skills = [
        step["skill"]
        for step in steps
    ]

    unknown_skills = [
        skill
        for skill in completed_skills
        if skill not in path_skills
    ]

    if unknown_skills:
        unknown_names = ", ".join(
            unknown_skills
        )

        raise ValueError(
            f"Skill not found in learning path: "
            f"{unknown_names}"
        )

    # Remove duplicate completed skills.
    completed_set = set(completed_skills)

    completed_in_order = [
        skill
        for skill in path_skills
        if skill in completed_set
    ]

    remaining_skills = [
        skill
        for skill in path_skills
        if skill not in completed_set
    ]

    total_steps = len(path_skills)
    completed_count = len(completed_in_order)

    if total_steps == 0:
        progress_percentage = 100.0
    else:
        progress_percentage = round(
            completed_count / total_steps * 100,
            2,
        )

    if progress_percentage == 100:
        status = "Completed"
    elif progress_percentage == 0:
        status = "Not Started"
    else:
        status = "In Progress"

    next_step = None

    if remaining_skills:
        next_skill = remaining_skills[0]

        next_step = next(
            step
            for step in steps
            if step["skill"] == next_skill
        )

    return {
        "total_steps": total_steps,
        "completed_count": completed_count,
        "remaining_count": (
            total_steps - completed_count
        ),
        "progress_percentage": progress_percentage,
        "completed_skills": completed_in_order,
        "remaining_skills": remaining_skills,
        "next_step": next_step,
        "status": status,
    }