from collections import deque


def generate_learning_order(
    target_skills,
    user_skills,
    prerequisite_graph
):
    """
    Generate a valid learning order for target skills.

    Breadth-first search collects required prerequisites.
    Topological sorting places prerequisites before
    dependent skills.
    """

    if not isinstance(target_skills, list):
        raise TypeError("target_skills must be a list.")

    if not isinstance(user_skills, dict):
        raise TypeError("user_skills must be a dictionary.")

    if not isinstance(prerequisite_graph, dict):
        raise TypeError(
            "prerequisite_graph must be a dictionary."
        )

    if not target_skills:
        return []

    # Remove duplicate target skills while preserving order.
    target_skills = list(dict.fromkeys(target_skills))
    target_set = set(target_skills)

    needed_skills = set(target_skills)
    needed_order = list(target_skills)
    search_queue = deque(target_skills)

    # BFS: collect prerequisites that the user has not learned.
    while search_queue:
        skill = search_queue.popleft()
        prerequisites = prerequisite_graph.get(skill, [])

        if not isinstance(prerequisites, list):
            raise TypeError(
                f"Prerequisites for {skill} must be a list."
            )

        for prerequisite in prerequisites:
            current_level = user_skills.get(prerequisite, 0)

            prerequisite_is_needed = (
                current_level <= 0
                or prerequisite in target_set
            )

            if (
                prerequisite_is_needed
                and prerequisite not in needed_skills
            ):
                needed_skills.add(prerequisite)
                needed_order.append(prerequisite)
                search_queue.append(prerequisite)

    # Build graph for topological sorting.
    adjacency = {
        skill: []
        for skill in needed_order
    }

    indegree = {
        skill: 0
        for skill in needed_order
    }

    for skill in needed_order:
        for prerequisite in prerequisite_graph.get(
            skill,
            []
        ):
            if prerequisite in needed_skills:
                adjacency[prerequisite].append(skill)
                indegree[skill] += 1

    ready_queue = deque(
        skill
        for skill in needed_order
        if indegree[skill] == 0
    )

    learning_order = []

    while ready_queue:
        skill = ready_queue.popleft()
        learning_order.append(skill)

        for dependent_skill in adjacency[skill]:
            indegree[dependent_skill] -= 1

            if indegree[dependent_skill] == 0:
                ready_queue.append(dependent_skill)

    if len(learning_order) != len(needed_skills):
        raise ValueError(
            "A circular skill dependency was detected."
        )

    return learning_order