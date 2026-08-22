import pytest

from algorithms.cosine_similarity import (
    calculate_cosine_similarity,
    similarity_percentage,
)


def test_identical_vectors():
    result = calculate_cosine_similarity(
        [8, 7, 6],
        [8, 7, 6]
    )

    assert result == pytest.approx(1.0)


def test_completely_different_vectors():
    result = calculate_cosine_similarity(
        [1, 0],
        [0, 1]
    )

    assert result == pytest.approx(0.0)


def test_zero_vector():
    result = calculate_cosine_similarity(
        [0, 0, 0],
        [5, 7, 8]
    )

    assert result == 0.0


def test_percentage_result():
    result = similarity_percentage(
        [8, 7, 6, 3, 2],
        [8, 7, 5, 9, 8]
    )

    assert 0 <= result <= 100


def test_different_vector_lengths():
    with pytest.raises(ValueError):
        calculate_cosine_similarity(
            [8, 7],
            [8, 7, 5]
        )