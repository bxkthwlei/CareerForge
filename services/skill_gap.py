def analyze_skill_gap(user_skills, required_skills):
    details = []

    for skill, required_level in required_skills.items():
        current_level = user_skills.get(skill, 0)
        gap = max(required_level - current_level, 0)

        if current_level >= required_level:
            status = "Matched"
        elif current_level == 0:
            status = "Missing"
        else:
            status = "Needs Improvement"

        details.append({
            "skill": skill,
            "current_level": current_level,
            "required_level": required_level,
            "gap": gap,
            "status": status
        })

    priority_gaps = sorted(
        [item for item in details if item["gap"] > 0],
        key=lambda item: item["gap"],
        reverse=True
    )

    matched_count = sum(
        item["status"] == "Matched"
        for item in details
    )

    total_skills = len(details)

    return {
        "skill_details": details,
        "priority_gaps": priority_gaps,
        "matched_count": matched_count,
        "total_skills": total_skills,
        "completion_percentage": round(
            matched_count / total_skills * 100,
            2
        ) if total_skills else 0.0
    }