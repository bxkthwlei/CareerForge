import pytest

from services.progress import (
    update_skill_progress,
    calculate_learning_progress,
)


USER_PROFILE = {
    "skills": {
        "networking": 8,
        "linux": 7,
        "cloud": 3,
    },
    "interests": [
        "networking",
    ],
}


LEARNING_PATH = {
    "total_steps": 4,
    "learning_path": [
        {
            "step": 1,
            "skill": "networking",
            "current_level": 8,
            "target_level": 9,
            "gap": 1,
        },
        {
            "step": 2,
            "skill": "routing_switching",
            "current_level": 6,
            "target_level": 9,
            "gap": 3,
        },
        {
            "step": 3,
            "skill": "cloud",
            "current_level": 3,
            "target_level": 5,
            "gap": 2,
        },
        {
            "step": 4,
            "skill": "network_security",
            "current_level": 6,
            "target_level": 7,
            "gap": 1,
        },
    ],
}


def test_update_existing_skill():
    result = update_skill_progress(
        USER_PROFILE,
        "cloud",
        5,
    )

    assert result["old_level"] == 3
    assert result["new_level"] == 5
    assert result["improvement"] == 2

    assert (
        result["updated_profile"]["skills"]["cloud"]
        == 5
    )


def test_add_new_skill():
    result = update_skill_progress(
        USER_PROFILE,
        "aws",
        4,
    )

    assert result["old_level"] == 0
    assert result["new_level"] == 4

    assert (
        result["updated_profile"]["skills"]["aws"]
        == 4
    )


def test_original_profile_is_unchanged():
    update_skill_progress(
        USER_PROFILE,
        "cloud",
        8,
    )

    assert USER_PROFILE["skills"]["cloud"] == 3


def test_skill_level_cannot_decrease():
    with pytest.raises(ValueError):
        update_skill_progress(
            USER_PROFILE,
            "networking",
            5,
        )


def test_invalid_skill_level():
    with pytest.raises(ValueError):
        update_skill_progress(
            USER_PROFILE,
            "cloud",
            11,
        )


def test_partial_learning_progress():
    result = calculate_learning_progress(
        LEARNING_PATH,
        [
            "networking",
            "routing_switching",
        ],
    )

    assert result["total_steps"] == 4
    assert result["completed_count"] == 2
    assert result["remaining_count"] == 2
    assert result["progress_percentage"] == 50.0
    assert result["status"] == "In Progress"
    assert result["next_step"]["skill"] == "cloud"


def test_completed_learning_path():
    result = calculate_learning_progress(
        LEARNING_PATH,
        [
            "networking",
            "routing_switching",
            "cloud",
            "network_security",
        ],
    )

    assert result["progress_percentage"] == 100.0
    assert result["status"] == "Completed"
    assert result["next_step"] is None


def test_unknown_completed_skill():
    with pytest.raises(
        ValueError,
        match="Skill not found",
    ):
        calculate_learning_progress(
            LEARNING_PATH,
            ["unknown_skill"],
        )