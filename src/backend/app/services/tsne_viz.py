import json
from pathlib import Path

import numpy as np

_TSNE_DIR = Path(__file__).parent.parent.parent / "data" / "tsne"


def compute_tsne(
    embeddings: np.ndarray,
    labels: list[str] | None = None,
    perplexity: int = 30,
    random_state: int = 42,
    sample_size: int = 5000,
) -> dict:
    from sklearn.manifold import TSNE

    if len(embeddings) > sample_size:
        indices = np.random.choice(len(embeddings), sample_size, replace=False)
        embeddings = embeddings[indices]
        if labels:
            labels = [labels[i] for i in indices]

    tsne = TSNE(
        n_components=2,
        perplexity=min(perplexity, max(5, len(embeddings) // 3)),
        random_state=random_state,
        n_iter=1000,
        verbose=0,
    )
    coords = tsne.fit_transform(embeddings.astype(np.float64))

    result = {
        "n_samples": int(len(coords)),
        "x": coords[:, 0].tolist(),
        "y": coords[:, 1].tolist(),
    }
    if labels:
        result["labels"] = labels

    return result


def save_tsne(data: dict, name: str = "tsne_coords") -> Path:
    _TSNE_DIR.mkdir(parents=True, exist_ok=True)
    path = _TSNE_DIR / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False))
    return path


def load_tsne(name: str = "tsne_coords") -> dict | None:
    path = _TSNE_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())
