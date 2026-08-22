from numbers import Real


def validate_percentage(name, value):
    if not isinstance(value, Real):
        raise TypeError(f"{name} must be numeric.")

    if not 0 <= value <= 100:
        raise ValueError(
            f"{name} must be between 0 and 100."
        )


def calculate_readiness(
    technical_score,
    completion_score,
    interest_score,
    completed_projects=0,
    target_projects=2
):
    """
    Calculate overall career readiness.

    Technical proficiency:  50%
    Requirements completed: 20%
    Interest alignment:     15%
    Practical projects:     15%
    """

    validate_percentage(
        "technical_score",
        technical_score
    )

    validate_percentage(
        "completion_score",
        completion_score
    )

    validate_percentage(
        "interest_score",
        interest_score
    )

    if not isinstance(completed_projects, int):
        raise TypeError(
            "completed_projects must be an integer."
        )

    if completed_projects < 0:
        raise ValueError(
            "completed_projects cannot be negative."
        )

    if not isinstance(target_projects, int):
        raise TypeError(
            "target_projects must be an integer."
        )

    if target_projects <= 0:
        raise ValueError(
            "target_projects must be greater than zero."
        )

    project_score = round(
        min(
            completed_projects / target_projects,
            1.0
        ) * 100,
        2
    )

    overall_score = round(
        (technical_score * 0.50)
        + (completion_score * 0.20)
        + (interest_score * 0.15)
        + (project_score * 0.15),
        2
    )

    if overall_score >= 80:
        readiness_level = "Ready"
    elif overall_score >= 60:
        readiness_level = "Nearly Ready"
    elif overall_score >= 40:
        readiness_level = "Developing"
    else:
        readiness_level = "Starting"

    return {
        "technical_score": technical_score,
        "completion_score": completion_score,
        "interest_score": interest_score,
        "project_score": project_score,
        "overall_score": overall_score,
        "readiness_level": readiness_level
    }