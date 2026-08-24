"""Streamlit dashboard for CareerForge."""

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.db import (  # noqa: E402
    get_progress_history,
    initialize_database,
    load_profile,
    record_skill_progress,
    save_profile,
)
from services.comparison import compare_careers  # noqa: E402
from services.learning_path import generate_learning_path  # noqa: E402
from services.progress import update_skill_progress  # noqa: E402
from services.readiness import calculate_readiness  # noqa: E402
from services.recommendation import recommend_careers  # noqa: E402
from services.roadmap import generate_roadmap  # noqa: E402
from services.skill_gap import analyze_skill_gap  # noqa: E402
from services.what_if import simulate_skill_change  # noqa: E402


DATABASE_PATH = PROJECT_ROOT / "database" / "careerforge.db"
CAREERS_PATH = PROJECT_ROOT / "data" / "careers.json"
SKILLS_PATH = PROJECT_ROOT / "data" / "skills.json"
PROFILE_NAME = "demo_user"
CAREER_COUNT = 30


DEFAULT_PROFILE = {
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


def load_json(path):
    """Load a UTF-8 JSON file."""

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def readable_name(identifier):
    """Convert an internal identifier into a label."""

    return identifier.replace("_", " ").title()


def initialize_app_state():
    """Initialize the database and Streamlit session."""

    initialize_database(DATABASE_PATH)
    stored_profile = load_profile(PROFILE_NAME, DATABASE_PATH)

    if stored_profile is None:
        save_profile(
            PROFILE_NAME,
            DEFAULT_PROFILE,
            DATABASE_PATH,
        )
        stored_profile = DEFAULT_PROFILE

    if "user_profile" not in st.session_state:
        st.session_state.user_profile = stored_profile

    if "selected_skills" not in st.session_state:
        st.session_state.selected_skills = list(
            stored_profile.get("skills", {}).keys()
        )


def render_profile_editor(skill_catalog, careers):
    """Render the profile form in the sidebar."""

    profile = st.session_state.user_profile
    skill_names = {
        item["id"]: item["name"]
        for item in skill_catalog
    }
    all_skill_ids = list(skill_names)
    all_interests = sorted(
        {
            interest
            for career in careers
            for interest in career["interests"]
        }
    )

    st.sidebar.header("User Profile")
    st.sidebar.caption(f"Saved profile: {PROFILE_NAME}")

    selected_skills = st.sidebar.multiselect(
        "Skills to assess",
        options=all_skill_ids,
        default=st.session_state.selected_skills,
        format_func=lambda skill: skill_names[skill],
    )
    st.session_state.selected_skills = selected_skills

    with st.sidebar.form("profile_form"):
        skill_levels = {}

        for skill in selected_skills:
            skill_levels[skill] = st.slider(
                skill_names[skill],
                min_value=0,
                max_value=10,
                value=int(
                    profile.get("skills", {}).get(skill, 0)
                ),
                key=f"profile_skill_{skill}",
            )

        interests = st.multiselect(
            "Interests",
            options=all_interests,
            default=[
                item
                for item in profile.get("interests", [])
                if item in all_interests
            ],
            format_func=readable_name,
        )
        completed_projects = st.number_input(
            "Completed projects",
            min_value=0,
            max_value=20,
            value=int(profile.get("completed_projects", 0)),
        )
        available_months = st.number_input(
            "Available months",
            min_value=1,
            max_value=24,
            value=int(profile.get("available_months", 4)),
        )
        weekly_hours = st.number_input(
            "Weekly study hours",
            min_value=1,
            max_value=80,
            value=int(profile.get("weekly_hours", 8)),
        )

        submitted = st.form_submit_button(
            "Save and Recalculate",
            use_container_width=True,
        )

    if submitted:
        updated_profile = {
            "skills": skill_levels,
            "interests": interests,
            "completed_projects": int(completed_projects),
            "available_months": int(available_months),
            "weekly_hours": int(weekly_hours),
        }
        save_profile(
            PROFILE_NAME,
            updated_profile,
            DATABASE_PATH,
        )
        st.session_state.user_profile = updated_profile
        st.session_state.pop("what_if_result", None)
        st.sidebar.success("Profile saved.")

    return st.session_state.user_profile


def build_analysis(profile):
    """Build the main analysis for the current profile."""

    recommendations = recommend_careers(profile, limit=5)

    if not recommendations:
        return None

    top_career = recommendations[0]
    gap_result = analyze_skill_gap(
        profile["skills"],
        top_career["required_skills"],
    )
    readiness = calculate_readiness(
        technical_score=top_career["weighted_score"],
        completion_score=gap_result["completion_percentage"],
        interest_score=top_career["interest_score"],
        completed_projects=profile.get("completed_projects", 0),
        target_projects=top_career.get("target_projects", 2),
    )
    learning_path = generate_learning_path(
        profile["skills"],
        top_career["required_skills"],
    )
    roadmap = generate_roadmap(
        user_skills=profile["skills"],
        required_skills=top_career["required_skills"],
        available_months=profile.get("available_months", 4),
        weekly_hours=profile.get("weekly_hours", 8),
    )

    return {
        "recommendations": recommendations,
        "top_career": top_career,
        "gap": gap_result,
        "readiness": readiness,
        "learning_path": learning_path,
        "roadmap": roadmap,
    }


def render_overview(analysis):
    """Render top-level metrics and recommendations."""

    top = analysis["top_career"]
    readiness = analysis["readiness"]
    gap = analysis["gap"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Top Career", top["name"])
    metric_columns[1].metric("Career Match", f"{top['final_score']}%")
    metric_columns[2].metric(
        "Readiness",
        f"{readiness['overall_score']}%",
    )
    metric_columns[3].metric(
        "Requirements Completed",
        f"{gap['completion_percentage']}%",
    )

    chart_data = pd.DataFrame(
        {
            "Career": [
                item["name"]
                for item in analysis["recommendations"]
            ],
            "Score": [
                item["final_score"]
                for item in analysis["recommendations"]
            ],
        }
    ).set_index("Career")

    st.subheader("Top Career Matches")
    st.bar_chart(chart_data)

    recommendation_rows = [
        {
            "Rank": position,
            "Career": career["name"],
            "Category": career["category"],
            "Final Score": career["final_score"],
            "Cosine": career["cosine_score"],
            "Weighted Skills": career["weighted_score"],
            "Interest": career["interest_score"],
        }
        for position, career in enumerate(
            analysis["recommendations"],
            start=1,
        )
    ]
    st.dataframe(
        pd.DataFrame(recommendation_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_skill_gap(analysis):
    """Render skill gaps and readiness."""

    gap = analysis["gap"]
    readiness = analysis["readiness"]

    st.subheader(f"Skill Gap — {analysis['top_career']['name']}")
    gap_rows = [
        {
            "Skill": readable_name(item["skill"]),
            "Current": item["current_level"],
            "Required": item["required_level"],
            "Gap": item["gap"],
            "Status": item["status"],
        }
        for item in gap["skill_details"]
    ]
    st.dataframe(
        pd.DataFrame(gap_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Career Readiness")
    columns = st.columns(5)
    columns[0].metric("Technical", f"{readiness['technical_score']}%")
    columns[1].metric("Completion", f"{readiness['completion_score']}%")
    columns[2].metric("Interest", f"{readiness['interest_score']}%")
    columns[3].metric("Projects", f"{readiness['project_score']}%")
    columns[4].metric("Overall", f"{readiness['overall_score']}%")
    st.info(f"Readiness level: {readiness['readiness_level']}")


def render_learning_and_roadmap(analysis):
    """Render the learning path and monthly roadmap."""

    learning_path = analysis["learning_path"]
    roadmap = analysis["roadmap"]

    st.subheader("AI Learning Path")

    if learning_path["learning_path"]:
        path_rows = [
            {
                "Step": item["step"],
                "Skill": readable_name(item["skill"]),
                "Current": item["current_level"],
                "Target": item["target_level"],
                "Gap": item["gap"],
                "Reason": item["reason"],
            }
            for item in learning_path["learning_path"]
        ]
        st.dataframe(
            pd.DataFrame(path_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("All required skills have been achieved.")

    st.subheader("Personalized Roadmap")
    roadmap_columns = st.columns(4)
    roadmap_columns[0].metric(
        "Months",
        roadmap["available_months"],
    )
    roadmap_columns[1].metric(
        "Weekly Hours",
        roadmap["weekly_hours"],
    )
    roadmap_columns[2].metric(
        "Estimated Hours",
        roadmap["total_estimated_hours"],
    )
    roadmap_columns[3].metric(
        "Feasible",
        "Yes" if roadmap["feasible"] else "No",
    )

    roadmap_rows = []
    for month in roadmap["months"]:
        if not month["activities"]:
            roadmap_rows.append(
                {
                    "Month": month["month"],
                    "Skill": "Review and practice",
                    "Levels": "-",
                    "Hours": 0,
                }
            )

        for activity in month["activities"]:
            roadmap_rows.append(
                {
                    "Month": month["month"],
                    "Skill": readable_name(activity["skill"]),
                    "Levels": (
                        f"{activity['current_level']} → "
                        f"{activity['target_level']}"
                    ),
                    "Hours": activity["estimated_hours"],
                }
            )

    st.dataframe(
        pd.DataFrame(roadmap_rows),
        use_container_width=True,
        hide_index=True,
    )

    for warning in roadmap["warnings"]:
        st.warning(warning)


def render_what_if(profile, skill_catalog):
    """Render the What-If Simulator."""

    st.subheader("What-If Simulator")
    skill_names = {
        item["id"]: item["name"]
        for item in skill_catalog
    }
    skill = st.selectbox(
        "Skill to improve",
        options=list(skill_names),
        format_func=lambda item: skill_names[item],
    )
    current_level = int(profile.get("skills", {}).get(skill, 0))
    target_levels = list(range(current_level, 11))
    new_level = st.select_slider(
        "New level",
        options=target_levels,
        value=target_levels[-1],
    )

    if st.button(
        "Run Simulation",
        disabled=new_level == current_level,
    ):
        st.session_state.what_if_result = simulate_skill_change(
            profile,
            skill,
            new_level,
            limit=CAREER_COUNT,
        )

    result = st.session_state.get("what_if_result")

    if not result:
        return

    biggest = result["biggest_improvement"]
    if biggest:
        st.success(
            f"Biggest improvement: {biggest['name']} "
            f"(+{biggest['score_change']}%)"
        )

    changed_rows = [
        {
            "Career": item["name"],
            "Before": item["before_score"],
            "After": item["after_score"],
            "Change": item["score_change"],
            "Rank Before": item["before_rank"],
            "Rank After": item["after_rank"],
        }
        for item in result["career_changes"]
        if item["score_change"] != 0
    ]
    st.dataframe(
        pd.DataFrame(changed_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_comparison(profile, careers):
    """Render side-by-side career comparison."""

    st.subheader("Career Comparison")
    career_names = [career["name"] for career in careers]
    first = st.selectbox(
        "First career",
        career_names,
        index=career_names.index("Network Engineer"),
    )
    second = st.selectbox(
        "Second career",
        career_names,
        index=career_names.index("SOC Analyst"),
    )

    if first == second:
        st.warning("Choose two different careers.")
        return

    result = compare_careers(profile, first, second)
    first_result = result["career_a"]
    second_result = result["career_b"]

    comparison_rows = [
        {
            "Metric": "Overall score",
            first: first_result["final_score"],
            second: second_result["final_score"],
        },
        {
            "Metric": "Cosine similarity",
            first: first_result["cosine_score"],
            second: second_result["cosine_score"],
        },
        {
            "Metric": "Weighted skills",
            first: first_result["weighted_score"],
            second: second_result["weighted_score"],
        },
        {
            "Metric": "Interest match",
            first: first_result["interest_score"],
            second: second_result["interest_score"],
        },
    ]
    st.dataframe(
        pd.DataFrame(comparison_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.success(
        f"Overall winner: {result['overall_winner']} "
        f"(difference {result['score_difference']}%)"
    )


def render_progress(profile, analysis):
    """Render saved progress and complete the next skill."""

    st.subheader("Progress Tracking")
    gap = analysis["gap"]
    st.progress(gap["completion_percentage"] / 100)
    st.write(
        f"Requirements completed: "
        f"{gap['matched_count']}/{gap['total_skills']} "
        f"({gap['completion_percentage']}%)"
    )

    history = get_progress_history(
        PROFILE_NAME,
        DATABASE_PATH,
    )

    if history:
        history_rows = [
            {
                "Career": item["career_name"],
                "Skill": readable_name(item["skill"]),
                "Before": item["old_level"],
                "After": item["new_level"],
                "Improvement": item["improvement"],
                "Recorded": item["recorded_at"],
            }
            for item in history
        ]
        st.dataframe(
            pd.DataFrame(history_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No saved progress yet.")

    steps = analysis["learning_path"]["learning_path"]

    if not steps:
        st.success("Career learning path completed.")
        return

    next_step = steps[0]
    st.info(
        f"Next skill: {readable_name(next_step['skill'])} — "
        f"Level {next_step['current_level']} → "
        f"{next_step['target_level']}"
    )

    if st.button("Complete Next Skill"):
        update_result = update_skill_progress(
            profile,
            next_step["skill"],
            next_step["target_level"],
        )
        updated_profile = update_result["updated_profile"]

        duplicate = any(
            item["career_name"] == analysis["top_career"]["name"]
            and item["skill"] == next_step["skill"]
            and item["new_level"] == next_step["target_level"]
            for item in history
        )

        if not duplicate:
            record_skill_progress(
                profile_name=PROFILE_NAME,
                career_name=analysis["top_career"]["name"],
                skill=next_step["skill"],
                old_level=next_step["current_level"],
                new_level=next_step["target_level"],
                db_path=DATABASE_PATH,
            )

        save_profile(
            PROFILE_NAME,
            updated_profile,
            DATABASE_PATH,
        )
        st.session_state.user_profile = updated_profile
        st.session_state.pop("what_if_result", None)
        st.rerun()


def main():
    """Run the CareerForge Streamlit application."""

    st.set_page_config(
        page_title="CareerForge",
        page_icon="🎯",
        layout="wide",
    )
    initialize_app_state()

    careers = load_json(CAREERS_PATH)
    skill_catalog = load_json(SKILLS_PATH)
    profile = render_profile_editor(skill_catalog, careers)
    analysis = build_analysis(profile)

    st.title("CareerForge")
    st.caption("AI Career and Skill-Gap Planner")

    if analysis is None:
        st.error("No career recommendations were found.")
        return

    tabs = st.tabs(
        [
            "Overview",
            "Skill Gap",
            "Learning & Roadmap",
            "What-If",
            "Compare",
            "Progress",
        ]
    )

    with tabs[0]:
        render_overview(analysis)
    with tabs[1]:
        render_skill_gap(analysis)
    with tabs[2]:
        render_learning_and_roadmap(analysis)
    with tabs[3]:
        render_what_if(profile, skill_catalog)
    with tabs[4]:
        render_comparison(profile, careers)
    with tabs[5]:
        render_progress(profile, analysis)


if __name__ == "__main__":
    main()