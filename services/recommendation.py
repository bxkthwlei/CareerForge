import json
from pathlib import Path

from algorithms.cosine_similarity import similarity_percentage
from algorithms.weighted_scoring import calculate_weighted_score


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CAREERS_FILE = PROJECT_ROOT / "data" / "careers.json"


def load_careers(file_path=CAREERS_FILE):
    """Load career information from the JSON data file."""

    with open(file_path, "r", encoding="utf-8") as file:
        careers = json.load(file)

    if not isinstance(careers, list):
        raise ValueError("Career data must be a list.")

    return careers


def normalize_interest(value):
    """Convert an interest name into a consistent format."""

    return str(value).strip().lower().replace(" ", "_")


def calculate_interest_match(user_interests, career_interests):
    """
    Calculate how many career interests match
    the user's interests.

    Returns a percentage between 0 and 100.
    """

    normalized_user_interests = {
        normalize_interest(interest)
        for interest in user_interests
    }

    normalized_career_interests = {
        normalize_interest(interest)
        for interest in career_interests
    }

    if not normalized_career_interests:
        return 0.0

    matched_interests = (
        normalized_user_interests
        & normalized_career_interests
    )

    return round(
        (
            len(matched_interests)
            / len(normalized_career_interests)
        ) * 100,
        2
    )


def score_career(user_skills, user_interests, career):
    """Calculate recommendation scores for one career."""

    required_skills = career.get("required_skills", {})
    career_interests = career.get("interests", [])

    skill_order = list(required_skills.keys())

    user_vector = [
        user_skills.get(skill, 0)
        for skill in skill_order
    ]

    career_vector = [
        required_skills[skill]
        for skill in skill_order
    ]

    cosine_score = similarity_percentage(
        user_vector,
        career_vector
    )

    weighted_score = calculate_weighted_score(
        user_skills,
        required_skills
    )

    interest_score = calculate_interest_match(
        user_interests,
        career_interests
    )

    final_score = round(
        (cosine_score * 0.40)
        + (weighted_score * 0.40)
        + (interest_score * 0.20),
        2
    )

    return {
        "id": career.get("id"),
        "name": career.get("name"),
        "category": career.get("category"),
        "description": career.get("description"),
        "required_skills": required_skills,
        "career_interests": career_interests,
        "cosine_score": cosine_score,
        "weighted_score": weighted_score,
        "interest_score": interest_score,
        "final_score": final_score
    }


def recommend_careers(user_profile, limit=5):
    """Rank careers according to the user's profile."""

    if not isinstance(user_profile, dict):
        raise TypeError("user_profile must be a dictionary.")

    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit must be a positive integer.")

    user_skills = user_profile.get("skills", {})
    user_interests = user_profile.get("interests", [])

    if not isinstance(user_skills, dict):
        raise TypeError("User skills must be a dictionary.")

    if not isinstance(user_interests, list):
        raise TypeError("User interests must be a list.")

    careers = load_careers()

    results = [
        score_career(
            user_skills,
            user_interests,
            career
        )
        for career in careers
    ]

    results.sort(
        key=lambda result: result["final_score"],
        reverse=True
    )

    return results[:limit]