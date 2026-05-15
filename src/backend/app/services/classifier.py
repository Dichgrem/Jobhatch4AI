from collections import Counter

import numpy as np
import torch
import torch.nn as nn

from app.services.preprocess import text_to_bow


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


def classify_from_text(
    model: MLPClassifier,
    texts: list[str],
    vocab: list[str],
    tokenize_fn,
) -> np.ndarray:
    device = next(model.parameters()).device
    vectors = np.array([text_to_bow(tokenize_fn(t), vocab) for t in texts])
    x = torch.tensor(vectors, dtype=torch.float32).to(device)
    preds, _ = model.predict(x)
    return preds


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
