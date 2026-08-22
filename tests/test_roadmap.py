import pytest

from algorithms.constraint_planner import (
    estimate_skill_hours,
    create_constraint_plan
)

from services.roadmap import generate_roadmap


def test_estimate_advanced_skill_hours():
    skill_step = {
        "skill": "routing_switching",
        "gap": 3,
        "target_level": 9
    }

    assert estimate_skill_hours(skill_step) == 27


def test_four_steps_are_allocated_to_four_months():
    learning_steps = [
        {
            "step": 1,
            "skill": "networking",
            "gap": 1,
            "target_level": 9
        },
        {
            "step": 2,
            "skill": "routing_switching",
            "gap": 3,
            "target_level": 9
        },
        {
            "step": 3,
            "skill": "cloud",
            "gap": 2,
            "target_level": 5
        },
        {
            "step": 4,
            "skill": "network_security",
            "gap": 1,
            "target_level": 7
        }
    ]

    result = create_constraint_plan(
        learning_steps,
        available_months=4,
        weekly_hours=8
    )

    assert result["months"][0]["activities"][0][
        "skill"
    ] == "networking"

    assert result["months"][1]["activities"][0][
        "skill"
    ] == "routing_switching"

    assert result["months"][2]["activities"][0][
        "skill"
    ] == "cloud"

    assert result["months"][3]["activities"][0][
        "skill"
    ] == "network_security"

    assert result["feasible"] is True


def test_overloaded_roadmap_is_not_feasible():
    learning_steps = [
        {
            "step": 1,
            "skill": "advanced_skill",
            "gap": 10,
            "target_level": 10
        }
    ]

    result = create_constraint_plan(
        learning_steps,
        available_months=1,
        weekly_hours=2
    )

    assert result["feasible"] is False
    assert len(result["warnings"]) == 1


def test_invalid_available_months():
    with pytest.raises(ValueError):
        create_constraint_plan(
            learning_steps=[],
            available_months=0,
            weekly_hours=8
        )


def test_network_engineer_roadmap():
    user_skills = {
        "networking": 8,
        "linux": 7,
        "routing_switching": 6,
        "network_security": 6,
        "cloud": 3,
        "python": 6
    }

    required_skills = {
        "networking": 9,
        "linux": 6,
        "routing_switching": 9,
        "network_security": 7,
        "cloud": 5,
        "python": 4
    }

    prerequisite_graph = {
        "routing_switching": ["networking"],
        "network_security": [
            "networking",
            "routing_switching"
        ],
        "cloud": [
            "linux",
            "networking"
        ]
    }

    result = generate_roadmap(
        user_skills=user_skills,
        required_skills=required_skills,
        available_months=4,
        weekly_hours=8,
        prerequisite_graph=prerequisite_graph
    )

    assert result["total_learning_steps"] == 4
    assert result["feasible"] is True

    assert result["months"][0]["activities"][0][
        "skill"
    ] == "networking"

    assert result["months"][3]["activities"][0][
        "skill"
    ] == "network_security"