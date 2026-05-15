from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


@router.get("/summary")
async def get_summary(
    total_jobs: int = Query(0),
    avg_salary: float = Query(0),
    top_skills: str = Query(""),
):
    skills = [s.strip() for s in top_skills.split(",") if s.strip()]
    return {
        "total_jobs": total_jobs,
        "avg_salary": avg_salary,
        "top_skills": skills,
    }


@router.get("/salary-distribution")
async def get_salary_distribution():
    return {
        "labels": ["0-10K", "10-20K", "20-30K", "30-40K", "40K+"],
        "data": [0, 0, 0, 0, 0],
    }


@router.get("/education-distribution")
async def get_education_distribution():
    return {
        "labels": ["大专", "本科", "硕士", "博士", "不限"],
        "data": [0, 0, 0, 0, 0],
    }


@router.get("/skill-wordcloud")
async def get_skill_wordcloud():
    return {"words": []}


@router.post("/analyze")
async def analyze_job_data(data: dict):
    from app.services.preprocess import tokenize, TECH_TERMS, extract_tech_terms

    texts = data.get("texts", [])
    if not texts:
        return {"top_skills": [], "summary": {}}

    all_tokens = [tokenize(t) for t in texts]

    all_extracted: list[str] = []
    for tokens in all_tokens:
        all_extracted.extend(extract_tech_terms(tokens, TECH_TERMS))

    from collections import Counter

    counter = Counter(all_extracted)
    top_skills = [{"skill": s, "count": c} for s, c in counter.most_common(20)]

    return {
        "top_skills": top_skills,
        "summary": {
            "total_docs": len(texts),
            "total_terms": len(all_tokens),
        },
    }


@router.post("/classify")
async def classify_text(data: dict):
    from app.services.preprocess import tokenize, build_vocab, text_to_bow
    from app.services.classifier import MLPClassifier

    texts = data.get("texts", [])
    labels = data.get("labels", [])
    if len(texts) < 3:
        raise HTTPException(status_code=400, detail="至少需要3条数据")

    tokens_list = [tokenize(t) for t in texts]
    vocab = build_vocab(tokens_list, min_freq=1, max_size=500)
    x = __import__("numpy").array([text_to_bow(t, vocab) for t in tokens_list])

    num_classes = max(len(set(labels)), 2) if labels else 3
    device = __import__("torch").device(
        "cuda" if __import__("torch").cuda.is_available() else "cpu"
    )

    model = MLPClassifier(len(vocab), hidden_dim=128, num_classes=num_classes).to(
        device
    )

    if labels:
        label_map = {label: i for i, label in enumerate(sorted(set(labels)))}
        y = __import__("numpy").array([label_map[label] for label in labels])
        from app.services.classifier import train_mlp

        history = train_mlp(model, x, y, epochs=10)
    else:
        history = []

    preds, _ = model.predict(
        __import__("torch").tensor(x, dtype=__import__("torch").float32).to(device)
    )

    return {
        "vocabulary_size": len(vocab),
        "num_samples": len(texts),
        "num_classes": num_classes,
        "predictions": preds.tolist(),
        "history": history,
    }
