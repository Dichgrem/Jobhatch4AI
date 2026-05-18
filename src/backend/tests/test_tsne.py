import numpy as np

from app.services.tsne_viz import compute_tsne, load_tsne, save_tsne


class TestTSNE:
    def test_compute_tsne(self):
        embeddings = np.random.randn(200, 1024).astype(np.float32)
        result = compute_tsne(embeddings, perplexity=30, sample_size=200)
        assert "x" in result
        assert "y" in result
        assert len(result["x"]) == 200
        assert len(result["y"]) == 200
        assert result["n_samples"] == 200

    def test_compute_tsne_with_labels(self):
        embeddings = np.random.randn(100, 64).astype(np.float32)
        labels = ["A"] * 50 + ["B"] * 50
        result = compute_tsne(embeddings, labels=labels)
        assert result["labels"] == labels

    def test_small_dataset(self):
        embeddings = np.random.randn(5, 64).astype(np.float32)
        result = compute_tsne(embeddings, perplexity=5)
        assert result["n_samples"] == 5

    def test_save_load(self):
        data = {"x": [1.0, 2.0], "y": [3.0, 4.0], "n_samples": 2}
        save_tsne(data, "test_tsne")
        loaded = load_tsne("test_tsne")
        assert loaded is not None
        assert loaded["x"] == [1.0, 2.0]
        assert loaded["y"] == [3.0, 4.0]

    def test_load_missing(self):
        assert load_tsne("no_such_tsne") is None
