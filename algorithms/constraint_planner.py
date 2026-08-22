from math import ceil
from numbers import Real


def estimate_skill_hours(skill_step):
    """
    Estimate learning hours using the skill gap
    and target difficulty.
    """

    if not isinstance(skill_step, dict):
        raise TypeError("skill_step must be a dictionary.")

    gap = skill_step.get("gap", 0)
    target_level = skill_step.get("target_level", 1)

    if not isinstance(gap, Real) or gap < 0:
        raise ValueError("Skill gap must be a non-negative number.")

    if (
        not isinstance(target_level, Real)
        or not 1 <= target_level <= 10
    ):
        raise ValueError(
            "Target level must be between 1 and 10."
        )

    if target_level <= 4:
        difficulty_multiplier = 1.0
    elif target_level <= 7:
        difficulty_multiplier = 1.25
    else:
        difficulty_multiplier = 1.5

    effective_gap = max(gap, 1)

    estimated_hours = ceil(
        effective_gap
        * 6
        * difficulty_multiplier
    )

    return max(4, estimated_hours)


def create_constraint_plan(
    learning_steps,
    available_months,
    weekly_hours
):
    """
    Allocate learning steps across available months.

    The planner considers:
    - Skill order
    - Skill gaps
    - Target difficulty
    - Available months
    - Weekly study hours
    """

    if not isinstance(learning_steps, list):
        raise TypeError("learning_steps must be a list.")

    if (
        not isinstance(available_months, int)
        or available_months <= 0
    ):
        raise ValueError(
            "available_months must be a positive integer."
        )

    if (
        not isinstance(weekly_hours, Real)
        or weekly_hours <= 0
    ):
        raise ValueError(
            "weekly_hours must be greater than zero."
        )

    monthly_capacity = round(weekly_hours * 4, 2)

    months = [
        {
            "month": month_number,
            "capacity_hours": monthly_capacity,
            "planned_hours": 0,
            "activities": []
        }
        for month_number in range(
            1,
            available_months + 1
        )
    ]

    total_steps = len(learning_steps)

    for index, step in enumerate(learning_steps):
        estimated_hours = estimate_skill_hours(step)

        if total_steps <= available_months:
            month_index = index
        else:
            month_index = min(
                (index * available_months) // total_steps,
                available_months - 1
            )

        activity = {
            "order": step.get("step", index + 1),
            "skill": step.get("skill"),
            "current_level": step.get(
                "current_level",
                0
            ),
            "target_level": step.get(
                "target_level",
                1
            ),
            "gap": step.get("gap", 0),
            "estimated_hours": estimated_hours,
            "reason": step.get(
                "reason",
                "Career skill gap"
            )
        }

        months[month_index]["activities"].append(
            activity
        )

        months[month_index]["planned_hours"] += (
            estimated_hours
        )

    warnings = []

    for month in months:
        month["planned_hours"] = round(
            month["planned_hours"],
            2
        )

        if (
            month["planned_hours"]
            > month["capacity_hours"]
        ):
            warnings.append(
                f"Month {month['month']} exceeds "
                f"the available study capacity."
            )

    total_estimated_hours = sum(
        month["planned_hours"]
        for month in months
    )

    total_capacity_hours = round(
        monthly_capacity * available_months,
        2
    )

    feasible = (
        total_estimated_hours <= total_capacity_hours
        and not warnings
    )

    return {
        "months": months,
        "monthly_capacity_hours": monthly_capacity,
        "total_estimated_hours": total_estimated_hours,
        "total_capacity_hours": total_capacity_hours,
        "feasible": feasible,
        "warnings": warnings
    }