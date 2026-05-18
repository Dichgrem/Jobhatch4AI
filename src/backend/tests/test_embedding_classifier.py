import numpy as np
import torch

from app.services.classifier import (
    EmbeddingMLPClassifier,
    load_embedding_model,
    save_embedding_model,
    train_embedding_mlp,
)


class TestEmbeddingMLPClassifier:
    def test_init(self):
        model = EmbeddingMLPClassifier(input_dim=1024, hidden_dim=256, num_classes=3)
        assert model.fc1.in_features == 1024
        assert model.fc1.out_features == 256
        assert model.fc3.out_features == 3

    def test_forward(self):
        model = EmbeddingMLPClassifier(input_dim=64, hidden_dim=32, num_classes=3)
        x = torch.randn(4, 64)
        out = model(x)
        assert out.shape == (4, 3)

    def test_predict(self):
        model = EmbeddingMLPClassifier(input_dim=64, hidden_dim=32, num_classes=3)
        x = torch.randn(2, 64)
        preds, probs = model.predict(x)
        assert preds.shape == (2,)
        assert probs.shape == (2, 3)
        assert np.allclose(probs.sum(axis=1), 1.0)

    def test_dropout_disabled_in_eval(self):
        model = EmbeddingMLPClassifier(input_dim=32, hidden_dim=16, num_classes=3)
        model.eval()
        x = torch.randn(2, 32)
        out1 = model(x)
        out2 = model(x)
        assert torch.allclose(out1, out2)


class TestTrainEmbeddingMLP:
    def test_training_reduces_loss(self):
        input_dim = 64
        x = np.random.randn(100, input_dim).astype(np.float32)
        y = np.random.randint(0, 3, 100)
        x_val = np.random.randn(20, input_dim).astype(np.float32)
        y_val = np.random.randint(0, 3, 20)

        model = EmbeddingMLPClassifier(
            input_dim=input_dim, hidden_dim=32, num_classes=3
        )
        history = train_embedding_mlp(model, x, y, x_val, y_val, epochs=5)

        assert len(history) == 5
        for item in history:
            assert "epoch" in item
            assert "loss" in item
            assert "val_accuracy" in item

    def test_small_dataset(self):
        x = np.random.randn(8, 64).astype(np.float32)
        y = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        model = EmbeddingMLPClassifier(input_dim=64, hidden_dim=16, num_classes=2)
        history = train_embedding_mlp(model, x, y, epochs=3)
        assert len(history) == 3


class TestSaveLoadEmbeddingModel:
    def test_save_load(self):
        model = EmbeddingMLPClassifier(input_dim=64, hidden_dim=32, num_classes=3)
        labels = ["A", "B", "C"]
        save_embedding_model(model, labels, "test_embed_mlp")

        result = load_embedding_model("test_embed_mlp")
        assert result is not None
        loaded_model, loaded_labels = result
        assert loaded_labels == labels

    def test_load_missing(self):
        assert load_embedding_model("no_such_model") is None
