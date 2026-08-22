import json
from pathlib import Path

from algorithms.graph_search import generate_learning_order
from services.skill_gap import analyze_skill_gap


PROJECT_ROOT = Path(__file__).resolve().parent.parent

PREREQUISITES_FILE = (
    PROJECT_ROOT
    / "data"
    / "prerequisites.json"
)


def load_prerequisites(file_path=PREREQUISITES_FILE):
    """Load the skill prerequisite graph."""

    with open(file_path, "r", encoding="utf-8") as file:
        prerequisites = json.load(file)

    if not isinstance(prerequisites, dict):
        raise ValueError(
            "Prerequisite data must be a dictionary."
        )

    return prerequisites


def generate_learning_path(
    user_skills,
    required_skills,
    prerequisite_graph=None
):
    """
    Generate a learning path from the user's
    priority skill gaps.
    """

    if not isinstance(user_skills, dict):
        raise TypeError("user_skills must be a dictionary.")

    if not isinstance(required_skills, dict):
        raise TypeError(
            "required_skills must be a dictionary."
        )

    if prerequisite_graph is None:
        prerequisite_graph = load_prerequisites()

    gap_result = analyze_skill_gap(
        user_skills,
        required_skills
    )

    target_skills = [
        item["skill"]
        for item in gap_result["priority_gaps"]
    ]

    learning_order = generate_learning_order(
        target_skills,
        user_skills,
        prerequisite_graph
    )

    learning_steps = []

    for step_number, skill in enumerate(
        learning_order,
        start=1
    ):
        current_level = user_skills.get(skill, 0)

        if skill in required_skills:
            target_level = required_skills[skill]
            reason = "Career skill gap"
        else:
            target_level = max(current_level, 1)
            reason = "Required prerequisite"

        learning_steps.append({
            "step": step_number,
            "skill": skill,
            "current_level": current_level,
            "target_level": target_level,
            "gap": max(
                target_level - current_level,
                0
            ),
            "reason": reason
        })

    return {
        "target_skills": target_skills,
        "total_steps": len(learning_steps),
        "learning_path": learning_steps
    }