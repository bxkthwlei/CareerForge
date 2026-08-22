import pytest

from services.reevaluation import (
    reevaluate_profile,
)


ORIGINAL_PROFILE = {
    "skills": {
        "networking": 8,
        "cybersecurity": 7,
    },
    "interests": [
        "networking",
        "cybersecurity",
    ],
    "completed_projects": 1,
}


UPDATED_PROFILE = {
    "skills": {
        "networking": 9,
        "cybersecurity": 7,
    },
    "interests": [
        "networking",
        "cybersecurity",
    ],
    "completed_projects": 1,
}


@pytest.fixture
def mock_services(monkeypatch):
    def fake_recommend_careers(
        user_profile,
        limit=100,
    ):
        networking_level = user_profile[
            "skills"
        ].get("networking", 0)

        careers = [
            {
                "name": "Network Engineer",
                "category": "Network and Systems",
                "final_score": (
                    68 + networking_level * 2
                ),
                "cosine_score": 90.0,
                "weighted_score": (
                    networking_level * 10
                ),
                "interest_score": 66.67,
                "required_skills": {
                    "networking": 9,
                },
                "target_projects": 2,
            },
            {
                "name": "SOC Analyst",
                "category": "Cybersecurity",
                "final_score": 85.0,
                "cosine_score": 89.0,
                "weighted_score": 75.0,
                "interest_score": 100.0,
                "required_skills": {
                    "cybersecurity": 8,
                },
                "target_projects": 2,
            },
        ]

        careers.sort(
            key=lambda career: career["final_score"],
            reverse=True,
        )

        return careers[:limit]

    def fake_analyze_skill_gap(
        user_skills,
        required_skills,
    ):
        details = []
        matched_count = 0

        for skill, required_level in (
            required_skills.items()
        ):
            current_level = user_skills.get(
                skill,
                0,
            )

            gap = max(
                required_level - current_level,
                0,
            )

            if gap == 0:
                matched_count += 1

            details.append(
                {
                    "skill": skill,
                    "current_level": current_level,
                    "required_level": required_level,
                    "gap": gap,
                    "status": (
                        "Matched"
                        if gap == 0
                        else "Needs Improvement"
                    ),
                }
            )

        total_skills = len(required_skills)

        completion = (
            round(
                matched_count
                / total_skills
                * 100,
                2,
            )
            if total_skills
            else 100.0
        )

        return {
            "matched_count": matched_count,
            "total_skills": total_skills,
            "completion_percentage": completion,
            "skill_details": details,
            "priority_gaps": [
                item
                for item in details
                if item["gap"] > 0
            ],
        }

    def fake_calculate_readiness(
        technical_score,
        completion_score,
        interest_score,
        completed_projects,
        target_projects,
    ):
        project_score = round(
            min(
                completed_projects
                / target_projects
                * 100,
                100,
            ),
            2,
        )

        overall_score = round(
            technical_score * 0.50
            + completion_score * 0.20
            + interest_score * 0.15
            + project_score * 0.15,
            2,
        )

        return {
            "technical_score": technical_score,
            "completion_score": completion_score,
            "interest_score": interest_score,
            "project_score": project_score,
            "overall_score": overall_score,
            "readiness_level": "Nearly Ready",
        }

    monkeypatch.setattr(
        "services.reevaluation.recommend_careers",
        fake_recommend_careers,
    )

    monkeypatch.setattr(
        "services.reevaluation.analyze_skill_gap",
        fake_analyze_skill_gap,
    )

    monkeypatch.setattr(
        "services.reevaluation.calculate_readiness",
        fake_calculate_readiness,
    )


def test_career_score_improves(mock_services):
    result = reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert result["changes"]["career_score"] == 2


def test_career_rank_improves(mock_services):
    result = reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert result["before"]["rank"] == 2
    assert result["after"]["rank"] == 1
    assert result["changes"]["rank_improvement"] == 1


def test_skill_gap_is_reduced(mock_services):
    result = reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert result["before"]["total_gap"] == 1
    assert result["after"]["total_gap"] == 0
    assert result["changes"]["gap_reduction"] == 1


def test_completion_percentage_improves(
    mock_services,
):
    result = reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert result["changes"]["completion"] == 100.0


def test_readiness_improves(mock_services):
    result = reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert result["changes"]["readiness"] > 0


def test_original_profile_is_not_modified(
    mock_services,
):
    reevaluate_profile(
        ORIGINAL_PROFILE,
        UPDATED_PROFILE,
        "Network Engineer",
    )

    assert (
        ORIGINAL_PROFILE["skills"]["networking"]
        == 8
    )


def test_unknown_career_is_invalid(mock_services):
    with pytest.raises(
        ValueError,
        match="Career not found",
    ):
        reevaluate_profile(
            ORIGINAL_PROFILE,
            UPDATED_PROFILE,
            "Unknown Career",
        )