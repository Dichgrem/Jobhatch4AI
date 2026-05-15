from collections import Counter

from app.services.recommender import recommend_skills, cosine_similarity
import numpy as np


class TestRecommendSkills:
    def test_basic_recommendation(self):
        user = ["python", "mysql"]
        counters = {
            "java": Counter({"java": 100, "spring": 80, "mysql": 60, "redis": 50}),
            "python": Counter({"python": 100, "django": 70, "tensorflow": 50}),
        }
        result = recommend_skills(user, counters, top_n=2)
        assert "java" in result
        assert "python" in result
        for skills in result.values():
            assert len(skills) <= 2

    def test_user_knows_everything(self):
        user = ["java", "spring", "mysql"]
        counters = {
            "java": Counter({"java": 100, "spring": 80, "mysql": 60}),
        }
        result = recommend_skills(user, counters, top_n=3)
        assert result["java"] == []

    def test_empty_user_skills(self):
        counters = {"java": Counter({"java": 100})}
        result = recommend_skills([], counters, top_n=1)
        assert result["java"][0][0] == "java"


class TestCosineSimilarity:
    def test_same_vectors(self):
        a = np.array([[1.0, 2.0, 3.0]])
        sim = cosine_similarity(a, a)
        assert np.allclose(sim[0, 0], 1.0)

    def test_orthogonal_vectors(self):
        a = np.array([[1.0, 0.0]])
        b = np.array([[0.0, 1.0]])
        sim = cosine_similarity(a, b)
        assert np.allclose(sim[0, 0], 0.0, atol=1e-6)

    def test_batch_shape(self):
        a = np.random.randn(10, 128).astype(np.float32)
        b = np.random.randn(5, 128).astype(np.float32)
        sim = cosine_similarity(a, b)
        assert sim.shape == (10, 5)

    def test_range(self):
        a = np.random.randn(100, 64).astype(np.float32)
        b = np.random.randn(50, 64).astype(np.float32)
        sim = cosine_similarity(a, b)
        assert np.all(sim >= -1.001)
        assert np.all(sim <= 1.001)
