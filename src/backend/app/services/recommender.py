from collections import Counter

import numpy as np


def recommend_skills(
    user_skills: list[str],
    job_skill_counters: dict[str, Counter],
    top_n: int = 5,
) -> dict[str, list[tuple[str, int]]]:
    recommendations: dict[str, list[tuple[str, int]]] = {}
    user_set = set(user_skills)

    for job_type, counter in job_skill_counters.items():
        missing = [
            (skill, count)
            for skill, count in counter.most_common()
            if skill not in user_set
        ]
        recommendations[job_type] = missing[:top_n]

    return recommendations


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a_norm = a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-8)
    b_norm = b / (np.linalg.norm(b, axis=-1, keepdims=True) + 1e-8)
    return np.dot(a_norm, b_norm.T)
