from services.skill_gap import analyze_skill_gap


def test_skill_gap_summary():
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

    result = analyze_skill_gap(
        user_skills,
        required_skills
    )

    assert result["matched_count"] == 2
    assert result["total_skills"] == 6
    assert result["completion_percentage"] == 33.33
    assert result["priority_gaps"][0]["skill"] == "routing_switching"
    assert result["priority_gaps"][0]["gap"] == 3


def test_missing_skill():
    result = analyze_skill_gap(
        {},
        {"python": 7}
    )

    skill = result["skill_details"][0]

    assert skill["current_level"] == 0
    assert skill["gap"] == 7
    assert skill["status"] == "Missing"


def test_no_skill_gap():
    result = analyze_skill_gap(
        {"python": 8},
        {"python": 7}
    )

    assert result["matched_count"] == 1
    assert result["completion_percentage"] == 100.0
    assert result["priority_gaps"] == []


def test_empty_requirements():
    result = analyze_skill_gap(
        {"python": 8},
        {}
    )

    assert result["matched_count"] == 0
    assert result["total_skills"] == 0
    assert result["completion_percentage"] == 0.0