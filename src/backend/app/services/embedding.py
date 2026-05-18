from pathlib import Path

import numpy as np

_EMBEDDING_MODEL = None
_EMBEDDING_DIM = 1024
_EMBEDDINGS_DIR = Path(__file__).parent.parent.parent / "data" / "embeddings"


def _get_model():
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer

        _EMBEDDING_MODEL = SentenceTransformer("BAAI/bge-m3", device="cpu")
    return _EMBEDDING_MODEL


def text_to_embedding(text: str) -> np.ndarray:
    model = _get_model()
    return model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0]


def batch_embed(
    texts: list[str],
    batch_size: int = 32,
    normalize: bool = True,
) -> np.ndarray:
    model = _get_model()
    return model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=normalize,
        show_progress_bar=True,
        convert_to_numpy=True,
    )


def save_embeddings(embeddings: np.ndarray, name: str = "job_embeddings") -> Path:
    _EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = _EMBEDDINGS_DIR / f"{name}.npy"
    np.save(str(path), embeddings)
    return path


def load_embeddings(name: str = "job_embeddings") -> np.ndarray | None:
    path = _EMBEDDINGS_DIR / f"{name}.npy"
    if not path.exists():
        return None
    return np.load(str(path))


def embedding_dim() -> int:
    return _EMBEDDING_DIM
