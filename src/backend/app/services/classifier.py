import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


MODEL_DIR = Path(__file__).parent.parent.parent / "data" / "models"


class MLPClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 256, num_classes: int = 3):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.fc2(self.dropout(self.relu(self.fc1(x))))

    def predict(self, x: torch.Tensor) -> tuple[np.ndarray, np.ndarray]:
        self.eval()
        with torch.no_grad():
            logits = self.forward(x)
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(probs, dim=1)
        return preds.numpy(), probs.numpy()


def save_model(
    model: MLPClassifier,
    vocab: list[str],
    label_names: list[str],
    name: str = "mlp_classifier",
) -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_DIR / f"{name}.pt")
    meta = {
        "input_dim": model.fc1.in_features,
        "hidden_dim": model.fc1.out_features,
        "num_classes": model.fc2.out_features,
        "vocab": vocab,
        "label_names": label_names,
    }
    (MODEL_DIR / f"{name}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2)
    )
    return MODEL_DIR / f"{name}.pt"


def load_model(
    name: str = "mlp_classifier",
) -> tuple[MLPClassifier, list[str], list[str]] | None:
    weights_path = MODEL_DIR / f"{name}.pt"
    meta_path = MODEL_DIR / f"{name}.json"
    if not weights_path.exists() or not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text())
    model = MLPClassifier(meta["input_dim"], meta["hidden_dim"], meta["num_classes"])
    model.load_state_dict(
        torch.load(str(weights_path), map_location="cpu", weights_only=True)
    )
    model.eval()
    return model, meta["vocab"], meta["label_names"]


def train_mlp(
    model: MLPClassifier,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray | None = None,
    y_val: np.ndarray | None = None,
    epochs: int = 20,
    lr: float = 0.001,
    batch_size: int = 32,
) -> list[dict]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    x_tensor = torch.tensor(x_train, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y_train, dtype=torch.long).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    history: list[dict] = []
    n_samples = len(x_train)

    for epoch in range(epochs):
        model.train()
        total_loss = 0.0

        indices = np.random.permutation(n_samples)
        for i in range(0, n_samples, batch_size):
            batch_idx = indices[i : i + batch_size]
            x_batch = x_tensor[batch_idx]
            y_batch = y_tensor[batch_idx]

            optimizer.zero_grad()
            logits = model(x_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(batch_idx)

        avg_loss = total_loss / n_samples
        metrics = {"epoch": epoch + 1, "loss": avg_loss}

        if x_val is not None and y_val is not None:
            model.eval()
            with torch.no_grad():
                x_val_t = torch.tensor(x_val, dtype=torch.float32).to(device)
                y_val_t = torch.tensor(y_val, dtype=torch.long).to(device)
                val_logits = model(x_val_t)
                val_preds = torch.argmax(val_logits, dim=1)
                val_acc = (val_preds == y_val_t).float().mean().item()
            metrics["val_accuracy"] = val_acc

        history.append(metrics)

    return history


def count_skills_by_category(
    token_lists: dict[str, list[list[str]]],
    tech_terms: list[str],
) -> dict[str, Counter]:
    tech_set = set(tech_terms)
    result: dict[str, Counter] = {}
    for category, tokens_list in token_lists.items():
        counter: Counter = Counter()
        for tokens in tokens_list:
            counter.update(t for t in tokens if t in tech_set)
        result[category] = counter
    return result
