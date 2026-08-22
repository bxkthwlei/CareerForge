import pytest

from services.readiness import calculate_readiness


def test_readiness_calculation():
    result = calculate_readiness(
        technical_score=80,
        completion_score=50,
        interest_score=100,
        completed_projects=1,
        target_projects=2
    )

    assert result["project_score"] == 50.0
    assert result["overall_score"] == 72.5
    assert result["readiness_level"] == "Nearly Ready"


def test_full_readiness():
    result = calculate_readiness(
        technical_score=100,
        completion_score=100,
        interest_score=100,
        completed_projects=3,
        target_projects=2
    )

    assert result["project_score"] == 100.0
    assert result["overall_score"] == 100.0
    assert result["readiness_level"] == "Ready"


def test_zero_readiness():
    result = calculate_readiness(
        technical_score=0,
        completion_score=0,
        interest_score=0,
        completed_projects=0,
        target_projects=2
    )

    assert result["overall_score"] == 0.0
    assert result["readiness_level"] == "Starting"


def test_invalid_percentage():
    with pytest.raises(ValueError):
        calculate_readiness(
            technical_score=110,
            completion_score=50,
            interest_score=50
        )


def test_invalid_target_projects():
    with pytest.raises(ValueError):
        calculate_readiness(
            technical_score=50,
            completion_score=50,
            interest_score=50,
            target_projects=0
        )