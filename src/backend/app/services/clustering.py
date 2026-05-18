from collections import Counter

import numpy as np
from sklearn.cluster import KMeans

from app.services.preprocess import (
    TECH_TERMS,
    build_vocab,
    extract_tech_terms,
    text_to_bow,
    tokenize,
)


def cluster_jobs(
    texts: list[str], n_clusters: int = 6, sample_size: int = 30000
) -> dict:
    if len(texts) > sample_size:
        indices = np.random.choice(len(texts), sample_size, replace=False)
        texts = [texts[i] for i in indices]

    tokens_list = [tokenize(t) for t in texts]
    vocab = build_vocab(tokens_list, min_freq=10, max_size=2000)
    vectors = np.array([text_to_bow(t, vocab) for t in tokens_list], dtype=np.float32)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    cluster_stats = []
    for c in range(n_clusters):
        mask = labels == c
        count = mask.sum()

        cluster_tokens: list[str] = []
        for tokens, is_in in zip(tokens_list, mask):
            if is_in:
                cluster_tokens.extend(extract_tech_terms(tokens, TECH_TERMS))

        skill_counter = Counter(cluster_tokens)
        top_skills = [
            {"skill": s, "count": c} for s, c in skill_counter.most_common(10)
        ]

        cluster_stats.append(
            {
                "cluster_id": c,
                "count": int(count),
                "percentage": round(count / len(texts) * 100, 1),
                "top_skills": top_skills,
            }
        )

    total_inertia = float(kmeans.inertia_)

    return {
        "n_clusters": n_clusters,
        "total_sampled": len(texts),
        "vocabulary_size": len(vocab),
        "inertia": total_inertia,
        "clusters": cluster_stats,
    }
