import numpy as np

from app.services.vector_search import (
    build_index,
    index_exists,
    save_texts,
    search,
)


class TestBuildAndSearch:
    def test_build_and_search(self):
        embeddings = np.random.randn(100, 1024).astype(np.float32)
        ids = [f"doc_{i}" for i in range(100)]
        info = build_index(embeddings, ids, "test_vs")
        assert info["total_vectors"] == 100
        assert index_exists("test_vs")

        query = np.random.randn(1024).astype(np.float32)
        results = search(query, top_k=5, name="test_vs")
        assert len(results) == 5
        assert "similarity" in results[0]
        assert "index" in results[0]
        assert results[0]["similarity"] >= results[-1]["similarity"]

    def test_search_with_texts(self):
        texts = ["Python Django开发", "Java Spring开发", "C++嵌入式"]
        embeddings = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float32,
        )
        save_texts(texts, "test_vs_text")
        build_index(embeddings, name="test_vs_text")

        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        results = search(query, top_k=1, name="test_vs_text")
        assert len(results) == 1
        assert "Python" in results[0]["text"]

    def test_index_exists_false(self):
        assert not index_exists("no_such_index")
