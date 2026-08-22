import pytest

from algorithms.graph_search import generate_learning_order
from services.learning_path import generate_learning_path


def test_prerequisite_comes_before_target():
    graph = {
        "siem": ["linux", "networking"],
        "linux": [],
        "networking": []
    }

    result = generate_learning_order(
        target_skills=["siem"],
        user_skills={
            "linux": 0,
            "networking": 5
        },
        prerequisite_graph=graph
    )

    assert result == ["linux", "siem"]


def test_learned_prerequisite_is_skipped():
    graph = {
        "siem": ["linux", "networking"]
    }

    result = generate_learning_order(
        target_skills=["siem"],
        user_skills={
            "linux": 5,
            "networking": 5
        },
        prerequisite_graph=graph
    )

    assert result == ["siem"]


def test_circular_dependency_detection():
    graph = {
        "skill_a": ["skill_b"],
        "skill_b": ["skill_a"]
    }

    with pytest.raises(ValueError):
        generate_learning_order(
            target_skills=["skill_a"],
            user_skills={},
            prerequisite_graph=graph
        )


def test_network_engineer_learning_path():
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

    graph = {
        "routing_switching": ["networking"],
        "network_security": [
            "networking",
            "routing_switching"
        ],
        "cloud": ["linux", "networking"]
    }

    result = generate_learning_path(
        user_skills,
        required_skills,
        graph
    )

    path = [
        step["skill"]
        for step in result["learning_path"]
    ]

    assert result["total_steps"] == 4
    assert path.index("networking") < path.index(
        "routing_switching"
    )
    assert path.index("networking") < path.index("cloud")
    assert path.index("routing_switching") < path.index(
        "network_security"
    )


def test_no_learning_path_when_all_skills_match():
    result = generate_learning_path(
        user_skills={
            "python": 8,
            "sql": 7
        },
        required_skills={
            "python": 7,
            "sql": 7
        },
        prerequisite_graph={}
    )

    assert result["target_skills"] == []
    assert result["total_steps"] == 0
    assert result["learning_path"] == []