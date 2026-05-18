import json
from pathlib import Path

import numpy as np
import torch
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.pipeline import load_pipeline_state, run_pipeline, save_pipeline_state

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@router.get("/summary")
async def get_summary():
    state = load_pipeline_state()
    return {
        "total_jobs": state["total_jobs"],
        "avg_salary": state["avg_salary"],
        "vocabulary_size": state["vocabulary_size"],
        "top_skills": [s["skill"] for s in state["top_skills"][:6]],
    }


@router.get("/salary-distribution")
async def get_salary_distribution():
    state = load_pipeline_state()
    return state["salary_distribution"]


@router.get("/education-distribution")
async def get_education_distribution():
    state = load_pipeline_state()
    return state["education_distribution"]


@router.get("/skill-wordcloud")
async def get_skill_wordcloud():
    state = load_pipeline_state()
    return {"words": state["wordcloud"]}


@router.get("/full-stats")
async def get_full_stats():
    return load_pipeline_state()


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="只支持 CSV 文件")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    saved_path = DATA_DIR / "recruitment_data.csv"
    content = await file.read()
    saved_path.write_bytes(content)

    try:
        state = run_pipeline(str(saved_path))
        save_pipeline_state(state)
        state["file"] = file.filename
        return state
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/analyze")
async def analyze_job_data(data: dict):
    from collections import Counter
    from app.services.preprocess import tokenize, TECH_TERMS, extract_tech_terms

    texts = data.get("texts", [])
    if not texts:
        return {"top_skills": [], "summary": {}}

    all_tokens = [tokenize(t) for t in texts]
    all_extracted: list[str] = []
    for tokens in all_tokens:
        all_extracted.extend(extract_tech_terms(tokens, TECH_TERMS))

    counter = Counter(all_extracted)
    top_skills = [{"skill": s, "count": c} for s, c in counter.most_common(20)]

    return {
        "top_skills": top_skills,
        "summary": {"total_docs": len(texts), "total_terms": len(all_tokens)},
    }


@router.post("/classify")
async def classify_text(data: dict):
    from app.services.preprocess import tokenize, build_vocab, text_to_bow
    from app.services.classifier import MLPClassifier
    import torch

    texts = data.get("texts", [])
    labels = data.get("labels", [])
    if len(texts) < 3:
        raise HTTPException(status_code=400, detail="至少需要3条数据")

    tokens_list = [tokenize(t) for t in texts]
    vocab = build_vocab(tokens_list, min_freq=1, max_size=500)
    x = torch.tensor([text_to_bow(t, vocab) for t in tokens_list], dtype=torch.float32)

    num_classes = max(len(set(labels)), 2) if labels else 3
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = MLPClassifier(len(vocab), hidden_dim=128, num_classes=num_classes).to(
        device
    )

    if labels:
        label_map = {label: i for i, label in enumerate(sorted(set(labels)))}
        import numpy as np

        y = np.array([label_map[label] for label in labels])
        from app.services.classifier import train_mlp

        history = train_mlp(model, x.numpy(), y, epochs=10)
    else:
        history = []

    preds, _ = model.predict(x.to(device))

    return {
        "vocabulary_size": len(vocab),
        "num_samples": len(texts),
        "num_classes": num_classes,
        "predictions": preds.tolist(),
        "history": history,
    }


@router.post("/train")
async def train_classifier(data: dict):
    from app.services.preprocess import tokenize, build_vocab, text_to_bow
    from app.services.classifier import MLPClassifier, save_model, train_mlp

    texts: list[str] = data.get("texts", [])
    labels: list[str] = data.get("labels", [])
    if len(texts) < 10:
        raise HTTPException(status_code=400, detail="至少需要10条训练数据")

    tokens_list = [tokenize(t) for t in texts]
    vocab = build_vocab(tokens_list, min_freq=2, max_size=1000)

    x = np.array([text_to_bow(t, vocab) for t in tokens_list], dtype=np.float32)

    unique_labels = sorted(set(labels))
    label_map = {label: i for i, label in enumerate(unique_labels)}
    y = np.array([label_map[label] for label in labels])

    split = int(len(x) * 0.8)
    x_train, x_val = x[:split], x[split:]
    y_train, y_val = y[:split], y[split:]

    model = MLPClassifier(len(vocab), hidden_dim=256, num_classes=len(unique_labels))
    history = train_mlp(model, x_train, y_train, x_val, y_val, epochs=20)

    path = save_model(model, vocab, unique_labels, "mlp_classifier")

    return {
        "model_path": str(path),
        "vocabulary_size": len(vocab),
        "num_classes": len(unique_labels),
        "label_names": unique_labels,
        "train_samples": len(x_train),
        "val_samples": len(x_val),
        "history": history,
    }


@router.post("/predict")
async def predict_text(data: dict):
    from app.services.preprocess import tokenize, text_to_bow
    from app.services.classifier import load_model

    texts: list[str] = data.get("texts", [])
    if not texts:
        raise HTTPException(status_code=400, detail="请提供待预测文本")

    result = load_model("mlp_classifier")
    if result is None:
        raise HTTPException(
            status_code=404, detail="未找到已训练模型，请先调用 /api/data/train"
        )

    model, vocab, label_names = result
    vectors = np.array(
        [text_to_bow(tokenize(t), vocab) for t in texts], dtype=np.float32
    )
    x = torch.tensor(vectors, dtype=torch.float32)
    preds, probs = model.predict(x)

    return {
        "predictions": [
            {"text": t, "label": label_names[p], "confidence": float(probs[i][p])}
            for i, (t, p) in enumerate(zip(texts, preds))
        ]
    }


@router.post("/cluster")
async def cluster_data(data: dict):
    from app.services.clustering import cluster_jobs
    from app.services.pipeline import load_pipeline_state

    n_clusters = data.get("n_clusters", 6)
    sample_size = data.get("sample_size", 30000)

    state = load_pipeline_state()
    if not state["total_jobs"]:
        raise HTTPException(status_code=400, detail="请先上传 CSV 数据")

    texts = _load_texts()
    if not texts:
        raise HTTPException(status_code=404, detail="未找到职位描述文本")

    result = cluster_jobs(texts, n_clusters, sample_size)

    from app.services.database import get_db

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO pipeline_state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        ("kmeans", json.dumps(result, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return result


def _load_texts() -> list[str]:
    import pandas as pd

    DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data"
    candidates = list(DATA_DIR.glob("*.csv"))
    if not candidates:
        return []

    df = None
    for enc in ["utf-8-sig", "utf-8", "gb18030", "gbk"]:
        try:
            df = pd.read_csv(str(candidates[0]), encoding=enc, nrows=50000)
            break
        except Exception:
            continue
    if df is None:
        return []

    col = None
    for c in ["职位描述", "keyword", "岗位要求", "JD"]:
        if c in df.columns:
            col = c
            break
    if col is None:
        return []

    return df[col].fillna("").tolist()


@router.get("/cluster")
async def get_cluster_result():
    from app.services.database import get_db

    conn = get_db()
    row = conn.execute(
        "SELECT value FROM pipeline_state WHERE key = 'kmeans'"
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row["value"])
    return {"n_clusters": 0, "clusters": []}


@router.post("/embed")
async def run_embedding_pipeline(data: dict):
    from app.services.embedding import batch_embed, save_embeddings
    from app.services.vector_search import build_index, save_texts

    texts = data.get("texts", [])
    if not texts:
        texts = _load_texts()
    if not texts:
        raise HTTPException(status_code=400, detail="请先上传数据或提供文本列表")

    max_samples = data.get("max_samples", 5000)
    if len(texts) > max_samples:
        indices = np.random.choice(len(texts), max_samples, replace=False)
        texts = [texts[i] for i in indices]

    embeddings = batch_embed(texts, batch_size=64, normalize=True)
    save_embeddings(embeddings, "job_embeddings")

    save_texts(texts, "job_index")

    ids = [f"job_{i}" for i in range(len(texts))]
    idx_info = build_index(embeddings, ids, "job_index")

    return {
        "total_embedded": len(texts),
        "embedding_dim": embeddings.shape[1],
        "index": idx_info,
    }


@router.get("/tsne")
async def get_tsne(force: bool = False, sample_size: int = 3000, perplexity: int = 30):
    from app.services.embedding import load_embeddings
    from app.services.tsne_viz import compute_tsne, save_tsne, load_tsne

    if not force:
        cached = load_tsne("tsne_coords")
        if cached:
            return cached

    embeddings = load_embeddings("job_embeddings")
    if embeddings is None:
        raise HTTPException(
            status_code=404,
            detail="未找到嵌入向量，请先调用 POST /api/data/embed",
        )

    result = compute_tsne(embeddings, sample_size=sample_size, perplexity=perplexity)
    save_tsne(result, "tsne_coords")
    return result


@router.post("/vector-search")
async def vector_search(data: dict):
    from app.services.embedding import text_to_embedding
    from app.services.vector_search import search, index_exists

    query = data.get("query", "")
    top_k = data.get("top_k", 5)

    if not query:
        raise HTTPException(status_code=400, detail="请提供查询文本")

    if not index_exists("job_index"):
        raise HTTPException(
            status_code=404,
            detail="未找到向量索引，请先调用 POST /api/data/embed",
        )

    query_vec = text_to_embedding(query)
    results = search(query_vec, top_k, "job_index")

    return {"query": query, "results": results, "total": len(results)}


@router.post("/train-embedding-mlp")
async def train_embedding_classifier(data: dict):
    from app.services.embedding import load_embeddings, batch_embed
    from app.services.classifier import (
        EmbeddingMLPClassifier,
        save_embedding_model,
        train_embedding_mlp,
    )

    texts: list[str] = data.get("texts", [])
    labels: list[str] = data.get("labels", [])

    if len(texts) < 10 or len(labels) < 10:
        raise HTTPException(status_code=400, detail="至少需要10条训练数据")

    embeddings_raw = load_embeddings("job_embeddings")
    if embeddings_raw is not None and len(embeddings_raw) >= len(texts):
        x = embeddings_raw[: len(texts)]
    else:
        x = batch_embed(texts, batch_size=64, normalize=True)

    unique_labels = sorted(set(labels))
    label_map = {lbl: i for i, lbl in enumerate(unique_labels)}
    y = np.array([label_map[lbl] for lbl in labels])

    split = int(len(x) * 0.8)
    x_train, x_val = x[:split], x[split:]
    y_train, y_val = y[:split], y[split:]

    num_classes = len(unique_labels)
    if num_classes < 2:
        raise HTTPException(
            status_code=400, detail="至少需要2个不同标签用于分类训练"
        )

    model = EmbeddingMLPClassifier(
        input_dim=x.shape[1],
        hidden_dim=512,
        num_classes=num_classes,
    )
    history = train_embedding_mlp(
        model, x_train, y_train, x_val, y_val, epochs=30
    )

    path = save_embedding_model(model, unique_labels, "embedding_mlp")

    return {
        "model_path": str(path),
        "input_dim": x.shape[1],
        "num_classes": num_classes,
        "label_names": unique_labels,
        "train_samples": len(x_train),
        "val_samples": len(x_val),
        "history": history,
    }


@router.post("/predict-embedding-mlp")
async def predict_embedding_classifier(data: dict):
    from app.services.embedding import text_to_embedding
    from app.services.classifier import load_embedding_model

    texts: list[str] = data.get("texts", [])
    if not texts:
        raise HTTPException(status_code=400, detail="请提供待预测文本")

    result = load_embedding_model("embedding_mlp")
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="未找到已训练的嵌入分类器，请先调用 POST /api/data/train-embedding-mlp",
        )

    model, label_names = result
    embeddings = np.array(
        [text_to_embedding(t) for t in texts], dtype=np.float32
    )
    x = torch.tensor(embeddings, dtype=torch.float32)
    preds, probs = model.predict(x)

    return {
        "predictions": [
            {
                "text": t,
                "label": label_names[p],
                "confidence": float(probs[i][p]),
            }
            for i, (t, p) in enumerate(zip(texts, preds))
        ]
    }
