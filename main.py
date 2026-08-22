import os
from pathlib import Path

from services.comparison import compare_careers
from services.recommendation import recommend_careers
from services.skill_gap import analyze_skill_gap
from services.readiness import calculate_readiness
from services.learning_path import generate_learning_path
from services.roadmap import generate_roadmap
from services.what_if import simulate_skill_change
from services.progress import (
    update_skill_progress,
    calculate_learning_progress,
)
from services.reevaluation import reevaluate_profile
from database.db import (
    initialize_database,
    save_profile,
    load_profile,
    record_skill_progress,
    get_progress_history,
)


CAREER_COUNT = 30
DISPLAY_LIMIT = 5
PROFILE_NAME = "demo_user"
DATABASE_PATH = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("CAREERFORGE_DB_PATH")
    or str(
        Path(__file__).resolve().parent
        / "database"
        / "careerforge.db"
    )
)


def format_skill_name(skill):
    """Convert a skill ID into a readable name."""

    return skill.replace("_", " ").title()


def format_change(value):
    """Format a positive or negative numeric change."""

    return f"+{value}" if value > 0 else str(value)


def display_recommendations(recommendations):
    """Display ranked career recommendations."""

    print("\nCareerForge — Top Career Recommendations\n")

    for position, career in enumerate(recommendations, start=1):
        print(
            f"{position}. {career['name']} "
            f"— {career['final_score']}%"
        )
        print(f"   Category: {career['category']}")
        print(f"   Cosine similarity: {career['cosine_score']}%")
        print(f"   Weighted skills: {career['weighted_score']}%")
        print(f"   Interest match: {career['interest_score']}%")
        print()


def display_skill_gap(user_skills, career):
    """Display skill-gap analysis for a career."""

    gap_result = analyze_skill_gap(
        user_skills,
        career["required_skills"],
    )

    print(f"\nSkill-Gap Analysis for {career['name']}\n")
    print(
        f"Matched requirements: "
        f"{gap_result['matched_count']}/"
        f"{gap_result['total_skills']}"
    )
    print(
        f"Requirement completion: "
        f"{gap_result['completion_percentage']}%\n"
    )

    for item in gap_result["skill_details"]:
        skill_name = format_skill_name(item["skill"])
        print(
            f"{skill_name:<22} "
            f"Current: {item['current_level']:<2} "
            f"Required: {item['required_level']:<2} "
            f"Gap: {item['gap']:<2} "
            f"{item['status']}"
        )

    print("\nPriority Skill Gaps")

    if not gap_result["priority_gaps"]:
        print("No skill gaps found.")
    else:
        for position, item in enumerate(
            gap_result["priority_gaps"],
            start=1,
        ):
            print(
                f"{position}. {format_skill_name(item['skill'])} "
                f"— Gap {item['gap']}"
            )

    return gap_result


def display_readiness(user_profile, career, gap_result):
    """Calculate and display career readiness."""

    readiness = calculate_readiness(
        technical_score=career["weighted_score"],
        completion_score=gap_result["completion_percentage"],
        interest_score=career["interest_score"],
        completed_projects=user_profile.get(
            "completed_projects",
            0,
        ),
        target_projects=career.get("target_projects", 2),
    )

    print(f"\nCareer Readiness for {career['name']}\n")
    print(f"Technical proficiency: {readiness['technical_score']}%")
    print(f"Requirements completed: {readiness['completion_score']}%")
    print(f"Interest alignment: {readiness['interest_score']}%")
    print(f"Practical projects: {readiness['project_score']}%")
    print(f"Overall readiness: {readiness['overall_score']}%")
    print(f"Readiness level: {readiness['readiness_level']}")

    return readiness


def display_learning_path(user_skills, career):
    """Generate and display an AI learning path."""

    result = generate_learning_path(
        user_skills,
        career["required_skills"],
    )

    print(f"\nAI Learning Path for {career['name']}\n")

    if not result["learning_path"]:
        print("All required skills have already been achieved.")
        return result

    print(f"Total learning steps: {result['total_steps']}\n")

    for item in result["learning_path"]:
        print(
            f"Step {item['step']}: "
            f"{format_skill_name(item['skill'])}"
        )
        print(f"   Current level: {item['current_level']}")
        print(f"   Target level: {item['target_level']}")
        print(f"   Skill gap: {item['gap']}")
        print(f"   Reason: {item['reason']}")
        print()

    return result


def display_roadmap(user_profile, career):
    """Generate and display a personalized roadmap."""

    result = generate_roadmap(
        user_skills=user_profile["skills"],
        required_skills=career["required_skills"],
        available_months=user_profile.get("available_months", 4),
        weekly_hours=user_profile.get("weekly_hours", 8),
    )

    print(f"\nPersonalized Roadmap for {career['name']}\n")
    print(f"Available time: {result['available_months']} months")
    print(f"Weekly study time: {result['weekly_hours']} hours")
    print(
        f"Estimated learning time: "
        f"{result['total_estimated_hours']} hours"
    )
    print(
        f"Available capacity: "
        f"{result['total_capacity_hours']} hours"
    )
    print(
        f"Roadmap feasible: "
        f"{'Yes' if result['feasible'] else 'No'}"
    )

    for month in result["months"]:
        print(f"\nMonth {month['month']}")

        if not month["activities"]:
            print("  Review and practice")
            continue

        for activity in month["activities"]:
            print(
                f"  - {format_skill_name(activity['skill'])} "
                f"({activity['estimated_hours']} hours)"
            )
            print(
                f"    Level {activity['current_level']} → "
                f"{activity['target_level']}"
            )

        print(
            f"  Planned workload: "
            f"{month['planned_hours']}/"
            f"{month['capacity_hours']} hours"
        )

    if result["warnings"]:
        print("\nRoadmap Warnings")
        for warning in result["warnings"]:
            print(f"- {warning}")

    return result


def display_progress(user_profile, career, completed_skills):
    """Display learning and skill progress."""

    learning_result = generate_learning_path(
        user_profile["skills"],
        career["required_skills"],
    )
    progress_result = calculate_learning_progress(
        learning_result,
        completed_skills,
    )

    # Each update creates a copy; the original profile is unchanged.
    updated_profile = user_profile

    print(f"\nProgress Tracking for {career['name']}\n")
    print(
        f"Completed steps: "
        f"{progress_result['completed_count']}/"
        f"{progress_result['total_steps']}"
    )
    print(f"Remaining steps: {progress_result['remaining_count']}")
    print(f"Progress: {progress_result['progress_percentage']}%")
    print(f"Status: {progress_result['status']}")

    if progress_result["completed_skills"]:
        print("\nCompleted Skills")

        for skill in progress_result["completed_skills"]:
            learning_step = next(
                item
                for item in learning_result["learning_path"]
                if item["skill"] == skill
            )
            update_result = update_skill_progress(
                updated_profile,
                skill,
                learning_step["target_level"],
            )
            updated_profile = update_result["updated_profile"]

            print(
                f"- {format_skill_name(skill)}: "
                f"Level {update_result['old_level']} → "
                f"{update_result['new_level']}"
            )

    if progress_result["remaining_skills"]:
        print("\nRemaining Skills")
        for skill in progress_result["remaining_skills"]:
            print(f"- {format_skill_name(skill)}")

    next_step = progress_result["next_step"]

    if next_step:
        print("\nNext Learning Step")
        print(f"Skill: {format_skill_name(next_step['skill'])}")
        print(f"Target level: {next_step['target_level']}")
        print(f"Skill gap: {next_step['gap']}")
    else:
        print("\nAll learning steps have been completed.")

    return {
        "progress": progress_result,
        "updated_profile": updated_profile,
    }


def display_reevaluation(original_profile, updated_profile, career_name):
    """Display dynamic career re-evaluation."""

    result = reevaluate_profile(
        original_profile,
        updated_profile,
        career_name,
        limit=CAREER_COUNT,
    )

    before = result["before"]
    after = result["after"]
    changes = result["changes"]
    before_career = before["recommendation"]
    after_career = after["recommendation"]
    before_readiness = before["readiness"]
    after_readiness = after["readiness"]
    before_gap = before["skill_gap"]
    after_gap = after["skill_gap"]

    print(f"\nDynamic Re-evaluation for {career_name}\n")
    print("Career Match")
    print(
        f"Score: {before_career['final_score']}% → "
        f"{after_career['final_score']}% "
        f"({format_change(changes['career_score'])}%)"
    )
    print(f"Rank: {before['rank']} → {after['rank']}")

    rank_improvement = changes["rank_improvement"]
    if rank_improvement > 0:
        print(f"Rank improvement: +{rank_improvement} position(s)")
    elif rank_improvement < 0:
        print(f"Rank change: {rank_improvement} position(s)")
    else:
        print("Rank change: No change")

    print("\nCareer Readiness")
    print(
        f"Readiness: {before_readiness['overall_score']}% → "
        f"{after_readiness['overall_score']}% "
        f"({format_change(changes['readiness'])}%)"
    )
    print(
        f"Readiness level: "
        f"{before_readiness['readiness_level']} → "
        f"{after_readiness['readiness_level']}"
    )

    print("\nSkill-Gap Improvement")
    print(
        f"Requirement completion: "
        f"{before_gap['completion_percentage']}% → "
        f"{after_gap['completion_percentage']}% "
        f"({format_change(changes['completion'])}%)"
    )
    print(f"Total skill gap: {before['total_gap']} → {after['total_gap']}")
    print(f"Gap reduction: {changes['gap_reduction']}")

    print("\nUpdated Top Career Rankings\n")
    for position, career in enumerate(
        result["updated_recommendations"][:DISPLAY_LIMIT],
        start=1,
    ):
        print(
            f"{position}. {career['name']} "
            f"— {career['final_score']}%"
        )

    return result


def display_database_storage(
    profile_name,
    original_profile,
    updated_profile,
    career_name,
    progress_result,
):
    """Save the profile and completed progress to the database."""

    initialize_database(DATABASE_PATH)

    stored_profile = load_profile(
        profile_name,
        DATABASE_PATH,
    )

    if stored_profile is None:
        save_profile(
            profile_name,
            original_profile,
            DATABASE_PATH,
        )

    existing_history = get_progress_history(
        profile_name,
        DATABASE_PATH,
    )

    new_records = 0

    for skill in progress_result["completed_skills"]:
        old_level = original_profile[
            "skills"
        ].get(skill, 0)
        new_level = updated_profile[
            "skills"
        ].get(skill, old_level)

        duplicate = any(
            entry["career_name"] == career_name
            and entry["skill"] == skill
            and entry["old_level"] == old_level
            and entry["new_level"] == new_level
            for entry in existing_history
        )

        if not duplicate:
            record_skill_progress(
                profile_name=profile_name,
                career_name=career_name,
                skill=skill,
                old_level=old_level,
                new_level=new_level,
                db_path=DATABASE_PATH,
            )
            new_records += 1

    save_profile(
        profile_name,
        updated_profile,
        DATABASE_PATH,
    )

    saved_profile = load_profile(
        profile_name,
        DATABASE_PATH,
    )
    history = get_progress_history(
        profile_name,
        DATABASE_PATH,
    )

    print("\nDatabase Storage\n")
    print(f"Profile: {profile_name}")
    print("Profile saved: Yes")
    print(f"New progress records: {new_records}")
    print(f"Total progress records: {len(history)}")

    if history:
        print("\nSaved Progress History")

        for position, entry in enumerate(
            history,
            start=1,
        ):
            print(
                f"{position}. "
                f"{format_skill_name(entry['skill'])}: "
                f"Level {entry['old_level']} → "
                f"{entry['new_level']} "
                f"({entry['career_name']})"
            )

    return {
        "profile": saved_profile,
        "history": history,
        "new_records": new_records,
    }


def display_what_if(user_profile, skill, new_level):
    """Display a hypothetical skill-change simulation."""

    # Calculate all 30 careers so before/after ranks remain accurate.
    result = simulate_skill_change(
        user_profile,
        skill,
        new_level,
        limit=CAREER_COUNT,
    )

    skill_name = format_skill_name(result["skill"])

    print("\nWhat-If Simulator\n")
    print(
        f"What if {skill_name} improves "
        f"from {result['old_level']} "
        f"to {result['new_level']}?\n"
    )
    print("Career Score Changes\n")

    changed_careers = [
        change
        for change in result["career_changes"]
        if change["score_change"] != 0
    ]

    if not changed_careers:
        print("No career scores were affected.")
    else:
        for change in changed_careers:
            print(
                f"{change['name']}: "
                f"{change['before_score']}% → "
                f"{change['after_score']}% "
                f"({format_change(change['score_change'])}%)"
            )
            print(
                f"   Rank: "
                f"{change['before_rank']} → "
                f"{change['after_rank']}"
            )

    biggest = result["biggest_improvement"]
    if biggest:
        print("\nBiggest Improvement")
        print(
            f"{biggest['name']}: "
            f"{format_change(biggest['score_change'])}%"
        )

    print("\nUpdated Top Career Rankings\n")
    for position, career in enumerate(
        result["after_recommendations"][:DISPLAY_LIMIT],
        start=1,
    ):
        print(
            f"{position}. {career['name']} "
            f"— {career['final_score']}%"
        )

    return result


def display_career_comparison(user_profile, first_career, second_career):
    """Compare and display two careers."""

    result = compare_careers(
        user_profile,
        first_career,
        second_career,
    )
    career_a = result["career_a"]
    career_b = result["career_b"]

    print("\nCareer Comparison\n")
    print(f"{first_career} vs {second_career}\n")

    first_width = max(22, len(first_career) + 3)
    second_width = max(22, len(second_career) + 3)

    print(
        f"{'Metric':<22}"
        f"{first_career:<{first_width}}"
        f"{second_career:<{second_width}}"
    )
    print("-" * (22 + first_width + second_width))
    print(
        f"{'Overall score':<22}"
        f"{str(career_a['final_score']) + '%':<{first_width}}"
        f"{str(career_b['final_score']) + '%':<{second_width}}"
    )
    print(
        f"{'Cosine similarity':<22}"
        f"{str(career_a['cosine_score']) + '%':<{first_width}}"
        f"{str(career_b['cosine_score']) + '%':<{second_width}}"
    )
    print(
        f"{'Weighted skills':<22}"
        f"{str(career_a['weighted_score']) + '%':<{first_width}}"
        f"{str(career_b['weighted_score']) + '%':<{second_width}}"
    )
    print(
        f"{'Interest match':<22}"
        f"{str(career_a['interest_score']) + '%':<{first_width}}"
        f"{str(career_b['interest_score']) + '%':<{second_width}}"
    )

    print("\nComparison Result")
    print(f"Overall winner: {result['overall_winner']}")
    print(f"Score difference: {result['score_difference']}%")

    winners = result["metric_winners"]
    print("\nMetric Winners")
    print(f"Cosine similarity: {winners['cosine_similarity']}")
    print(f"Weighted skills: {winners['weighted_score']}")
    print(f"Interest match: {winners['interest_match']}")

    return result


def main():
    """Run the CareerForge command-line demonstration."""

    user_profile = {
        "skills": {
            "python": 6,
            "linux": 7,
            "networking": 8,
            "cybersecurity": 7,
            "siem": 3,
            "incident_response": 2,
            "routing_switching": 6,
            "network_security": 6,
            "cloud": 3,
            "aws": 2,
            "docker": 3,
            "sql": 4,
            "statistics": 3,
            "data_visualization": 2,
            "excel": 5,
            "web_development": 3,
            "apis": 2,
            "databases": 4,
        },
        "interests": [
            "cybersecurity",
            "networking",
            "problem_solving",
        ],
        "completed_projects": 1,
        "available_months": 4,
        "weekly_hours": 8,
    }

    recommendations = recommend_careers(
        user_profile,
        limit=DISPLAY_LIMIT,
    )

    if not recommendations:
        print("No career recommendations were found.")
        return

    display_recommendations(recommendations)

    # The current profile still ranks Network Engineer first.
    top_career = recommendations[0]

    gap_result = display_skill_gap(
        user_profile["skills"],
        top_career,
    )
    display_readiness(user_profile, top_career, gap_result)
    display_learning_path(user_profile["skills"], top_career)
    display_roadmap(user_profile, top_career)

    progress_result = display_progress(
        user_profile,
        top_career,
        completed_skills=["networking"],
    )

    display_database_storage(
        profile_name=PROFILE_NAME,
        original_profile=user_profile,
        updated_profile=progress_result[
            "updated_profile"
        ],
        career_name=top_career["name"],
        progress_result=progress_result["progress"],
    )

    display_reevaluation(
        original_profile=user_profile,
        updated_profile=progress_result["updated_profile"],
        career_name=top_career["name"],
    )

    display_what_if(
        user_profile,
        skill="cloud",
        new_level=8,
    )

    display_career_comparison(
        user_profile,
        first_career="Network Engineer",
        second_career="SOC Analyst",
    )


if __name__ == "__main__":
    main()
