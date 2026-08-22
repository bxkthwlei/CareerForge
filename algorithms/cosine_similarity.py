from math import sqrt
from numbers import Real


def calculate_cosine_similarity(user_vector, career_vector):
    """
    Calculate similarity between a user's skill vector
    and a career's required-skill vector.

    Returns a score between 0.0 and 1.0.
    """

    if len(user_vector) != len(career_vector):
        raise ValueError("Vectors must have the same length.")

    if not user_vector:
        return 0.0

    all_values = list(user_vector) + list(career_vector)

    if not all(isinstance(value, Real) for value in all_values):
        raise TypeError("Vector values must be numbers.")

    dot_product = sum(
        user_value * career_value
        for user_value, career_value in zip(user_vector, career_vector)
    )

    user_magnitude = sqrt(
        sum(value ** 2 for value in user_vector)
    )

    career_magnitude = sqrt(
        sum(value ** 2 for value in career_vector)
    )

    if user_magnitude == 0 or career_magnitude == 0:
        return 0.0

    similarity = dot_product / (user_magnitude * career_magnitude)

    # Skill ratings are non-negative, so keep the result between 0 and 1.
    return max(0.0, min(1.0, similarity))


def similarity_percentage(user_vector, career_vector):
    """Return cosine similarity as a percentage."""

    similarity = calculate_cosine_similarity(
        user_vector,
        career_vector
    )

    return round(similarity * 100, 2)