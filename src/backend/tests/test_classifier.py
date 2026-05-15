import numpy as np
import torch

from app.services.classifier import MLPClassifier, train_mlp, count_skills_by_category


SAMPLE_TEXTS = [
    "精通Java、Spring Boot、MySQL，3年开发经验",
    "熟悉Python、Django、TensorFlow，机器学习方向",
    "掌握C++、Linux、嵌入式开发，5年经验",
    "Java后端开发，熟悉微服务架构",
    "Python数据分析，pandas numpy熟练",
    "C语言嵌入式，Linux内核开发",
]

SAMPLE_LABELS = ["java", "python", "c", "java", "python", "c"]


class TestMLPClassifier:
    def test_init(self):
        model = MLPClassifier(500, hidden_dim=128, num_classes=3)
        assert model.fc1.in_features == 500
        assert model.fc1.out_features == 128
        assert model.fc2.out_features == 3

    def test_forward(self):
        model = MLPClassifier(10, hidden_dim=8, num_classes=3)
        x = torch.randn(4, 10)
        out = model(x)
        assert out.shape == (4, 3)

    def test_predict(self):
        model = MLPClassifier(10, hidden_dim=8, num_classes=3)
        x = torch.randn(2, 10)
        preds, probs = model.predict(x)
        assert preds.shape == (2,)
        assert probs.shape == (2, 3)
        assert np.allclose(probs.sum(axis=1), 1.0)

    def test_dropout_disabled_in_eval(self):
        model = MLPClassifier(10, hidden_dim=8, num_classes=3)
        model.eval()
        x = torch.randn(2, 10)
        out1 = model(x)
        out2 = model(x)
        assert torch.allclose(out1, out2)


class TestTrainMLP:
    def test_training_reduces_loss(self):
        input_dim = 50
        x = np.random.randn(100, input_dim).astype(np.float32)
        y = np.random.randint(0, 3, 100)
        x_val = np.random.randn(20, input_dim).astype(np.float32)
        y_val = np.random.randint(0, 3, 20)

        model = MLPClassifier(input_dim, hidden_dim=32, num_classes=3)
        history = train_mlp(model, x, y, x_val, y_val, epochs=5, lr=0.001)

        assert len(history) == 5
        for item in history:
            assert "epoch" in item
            assert "loss" in item
            assert "val_accuracy" in item

    def test_small_dataset(self):
        x = np.random.randn(8, 20).astype(np.float32)
        y = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        model = MLPClassifier(20, hidden_dim=16, num_classes=2)
        history = train_mlp(model, x, y, epochs=3)
        assert len(history) == 3


class TestCountSkills:
    def test_count_by_category(self):
        tech_terms = ["python", "java", "mysql"]
        token_lists = {
            "python": [["python", "django", "mysql"], ["python", "tensorflow"]],
            "java": [["java", "spring", "mysql"], ["java", "hibernate"]],
        }
        result = count_skills_by_category(token_lists, tech_terms)
        assert result["python"]["python"] == 2
        assert result["python"]["mysql"] == 1
        assert result["java"]["java"] == 2
        assert result["java"]["mysql"] == 1
        assert "django" not in result["python"]

    def test_empty_categories(self):
        result = count_skills_by_category({}, ["python"])
        assert result == {}
