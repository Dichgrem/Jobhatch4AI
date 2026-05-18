import numpy as np

from app.services.embedding import (
    batch_embed,
    embedding_dim,
    load_embeddings,
    save_embeddings,
)


class TestEmbeddingDim:
    def test_returns_1024(self):
        assert embedding_dim() == 1024


class TestBatchEmbed:
    def test_output_shape(self):
        texts = ["Python开发工程师", "Java后端开发", "数据分析师"]
        embeddings = batch_embed(texts, batch_size=2, normalize=True)
        assert embeddings.shape == (3, 1024)
        assert embeddings.dtype == np.float32

    def test_normalized(self):
        texts = ["机器学习工程师", "深度学习研究员"]
        embeddings = batch_embed(texts, normalize=True)
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)


class TestSaveLoadEmbeddings:
    def test_roundtrip(self):
        embeddings = np.random.randn(10, 1024).astype(np.float32)
        save_embeddings(embeddings, "test_emb")
        loaded = load_embeddings("test_emb")
        assert loaded is not None
        assert loaded.shape == (10, 1024)
        assert np.allclose(loaded, embeddings)

    def test_missing_returns_none(self):
        loaded = load_embeddings("nonexistent")
        assert loaded is None
