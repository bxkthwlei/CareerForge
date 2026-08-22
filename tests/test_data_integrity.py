"""Validate CareerForge JSON data relationships."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "data"


def load_json(filename):
    with (DATA_DIRECTORY / filename).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


CAREERS = load_json("careers.json")
SKILLS = load_json("skills.json")
PREREQUISITES = load_json("prerequisites.json")


def test_exactly_thirty_careers():
    assert len(CAREERS) == 30


def test_career_ids_and_names_are_unique():
    career_ids = [career["id"] for career in CAREERS]
    career_names = [career["name"] for career in CAREERS]

    assert len(career_ids) == len(set(career_ids))
    assert len(career_names) == len(set(career_names))


def test_all_expected_categories_exist():
    categories = {
        career["category"]
        for career in CAREERS
    }

    assert categories == {
        "Cybersecurity",
        "Network and Systems",
        "Software Development",
        "AI and Data",
        "Cloud and DevOps",
        "Database",
        "UI/UX",
        "IT Management",
    }


def test_skill_ids_are_unique():
    skill_ids = [skill["id"] for skill in SKILLS]
    assert len(skill_ids) == len(set(skill_ids))


def test_career_requirements_reference_known_skills():
    known_skills = {skill["id"] for skill in SKILLS}

    for career in CAREERS:
        assert career["required_skills"]
        assert career["interests"]

        for skill, level in career[
            "required_skills"
        ].items():
            assert skill in known_skills, (
                f"Unknown skill {skill!r} in "
                f"{career['name']}"
            )
            assert isinstance(level, int)
            assert 1 <= level <= 10


def test_prerequisites_reference_known_skills():
    known_skills = {skill["id"] for skill in SKILLS}

    for skill, dependencies in (
        PREREQUISITES.items()
    ):
        assert skill in known_skills
        assert isinstance(dependencies, list)
        assert skill not in dependencies

        for dependency in dependencies:
            assert dependency in known_skills


def test_prerequisite_graph_has_no_cycles():
    visiting = set()
    visited = set()

    def visit(skill):
        if skill in visiting:
            raise AssertionError(
                f"Prerequisite cycle detected at {skill}"
            )

        if skill in visited:
            return

        visiting.add(skill)

        for dependency in PREREQUISITES.get(
            skill,
            [],
        ):
            visit(dependency)

        visiting.remove(skill)
        visited.add(skill)

    for skill in PREREQUISITES:
        visit(skill)