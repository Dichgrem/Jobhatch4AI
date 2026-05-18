import json
from pathlib import Path

import numpy as np

_INDEX_DIR = Path(__file__).parent.parent.parent / "data" / "vector_index"


def _cosine_similarity_chunked(
    query: np.ndarray, candidates: np.ndarray, top_k: int, chunk_size: int = 10000
) -> tuple[np.ndarray, np.ndarray]:
    query = query.reshape(1, -1)
    n = candidates.shape[0]

    if n <= chunk_size:
        sim = np.dot(candidates, query.T).ravel()
        indices = np.argsort(sim)[::-1][:top_k]
        return sim[indices], indices

    top_sims = np.full(top_k, -np.inf)
    top_indices = np.zeros(top_k, dtype=np.int64)

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        chunk = candidates[start:end]
        sim = np.dot(chunk, query.T).ravel()
        combined = np.concatenate([top_sims, sim])
        combined_idx = np.concatenate([top_indices, np.arange(start, end)])
        order = np.argsort(combined)[::-1][:top_k]
        top_sims = combined[order]
        top_indices = combined_idx[order]

    return top_sims, top_indices


def build_index(
    embeddings: np.ndarray,
    ids: list[str] | None = None,
    name: str = "job_index",
) -> dict:
    _INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(_INDEX_DIR / f"{name}_vectors.npy"), embeddings.astype(np.float32))

    if ids:
        (_INDEX_DIR / f"{name}_ids.json").write_text(
            json.dumps(ids, ensure_ascii=False)
        )

    return {
        "name": name,
        "dimension": int(embeddings.shape[1]),
        "total_vectors": int(embeddings.shape[0]),
    }


def search(
    query_embedding: np.ndarray,
    top_k: int = 5,
    name: str = "job_index",
) -> list[dict]:
    vectors_path = _INDEX_DIR / f"{name}_vectors.npy"
    if not vectors_path.exists():
        raise FileNotFoundError(f"Vector index not found: {vectors_path}")

    embeddings = np.load(str(vectors_path)).astype(np.float32)
    query = query_embedding.astype(np.float32)
    if query.ndim == 1:
        query = query.reshape(1, -1)

    distances, indices = _cosine_similarity_chunked(query, embeddings, top_k)

    results = []
    ids_path = _INDEX_DIR / f"{name}_ids.json"
    id_list = json.loads(ids_path.read_text()) if ids_path.exists() else []
    texts_path = _INDEX_DIR / f"{name}_texts.txt"

    texts = []
    if texts_path.exists():
        texts = texts_path.read_text(encoding="utf-8").split("\n---CHUNK---\n")

    for dist, idx in zip(distances, indices):
        entry = {"index": int(idx), "similarity": float(dist)}
        if idx < len(id_list):
            entry["id"] = id_list[idx]
        if idx < len(texts):
            entry["text"] = texts[idx][:500]
        results.append(entry)

    return results


def save_texts(texts: list[str], name: str = "job_index") -> Path:
    _INDEX_DIR.mkdir(parents=True, exist_ok=True)
    path = _INDEX_DIR / f"{name}_texts.txt"
    path.write_text("\n---CHUNK---\n".join(texts), encoding="utf-8")
    return path


def index_exists(name: str = "job_index") -> bool:
    return (_INDEX_DIR / f"{name}_vectors.npy").exists()
