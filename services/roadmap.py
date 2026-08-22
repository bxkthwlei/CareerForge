from algorithms.constraint_planner import (
    create_constraint_plan
)

from services.learning_path import (
    generate_learning_path
)


def generate_roadmap(
    user_skills,
    required_skills,
    available_months=4,
    weekly_hours=8,
    prerequisite_graph=None
):
    """
    Generate a personalized, time-constrained
    career learning roadmap.
    """

    learning_result = generate_learning_path(
        user_skills,
        required_skills,
        prerequisite_graph
    )

    constraint_result = create_constraint_plan(
        learning_result["learning_path"],
        available_months,
        weekly_hours
    )

    return {
        "available_months": available_months,
        "weekly_hours": weekly_hours,
        "total_learning_steps": learning_result[
            "total_steps"
        ],
        "target_skills": learning_result[
            "target_skills"
        ],
        "months": constraint_result["months"],
        "monthly_capacity_hours": constraint_result[
            "monthly_capacity_hours"
        ],
        "total_estimated_hours": constraint_result[
            "total_estimated_hours"
        ],
        "total_capacity_hours": constraint_result[
            "total_capacity_hours"
        ],
        "feasible": constraint_result["feasible"],
        "warnings": constraint_result["warnings"]
    }