import json
import re
from collections import Counter

import pandas as pd

from app.services.database import get_db, init_db
from app.services.preprocess import (
    TECH_TERMS,
    build_vocab,
    extract_tech_terms,
    tokenize,
)

init_db()

_STATE_KEY = "pipeline"


def auto_load_default_csv() -> bool:
    state = load_pipeline_state()
    if state["total_jobs"] > 0:
        return False

    data_dir = Path(__file__).parent.parent.parent.parent.parent / "data"
    candidates = sorted(data_dir.glob("*.csv"))
    if not candidates:
        return False

    run_pipeline(str(candidates[0]))
    return True


def run_pipeline(csv_path: str, text_column: str = "职位描述") -> dict:
    encodings = ["utf-8-sig", "utf-8", "gb18030", "gbk", "gb2312"]
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if df is None:
        raise ValueError(f"无法读取: {csv_path}")

    col = _find_column(
        df, [text_column, "keyword", "岗位要求", "职位描述", "JD"], str(df.columns[-1])
    )
    df["_text"] = df[col].fillna("")
    texts = df["_text"].tolist()

    tokens_list = [tokenize(t) for t in texts]
    vocab = build_vocab(tokens_list, min_freq=5, max_size=5000)
    all_extracted: list[str] = []
    for tokens in tokens_list:
        all_extracted.extend(extract_tech_terms(tokens, TECH_TERMS))
    tech_counter = Counter(all_extracted)

    salary_labels = ["0-10K", "10-15K", "15-20K", "20-30K", "30-40K", "40K+"]
    salary_bins = {label: 0 for label in salary_labels}

    edu_labels = ["大专", "本科", "硕士", "博士", "不限"]
    edu_counts = {}
    exp_labels = ["应届", "1-3年", "3-5年", "5-10年", "10年+", "不限"]
    exp_counts = {}

    salary_col = _find_column(
        df, ["salary", "薪资", "薪酬", "月薪", "最低月薪"], text_column
    )
    salary_col_high = _find_column(df, ["最高月薪"], text_column)
    edu_col = _find_column(df, ["education", "学历", "degree", "学历要求"], text_column)
    exp_col = _find_column(
        df, ["experience", "经验", "work_year", "要求经验"], text_column
    )

    total_salary = 0.0
    salary_count = 0

    for _, row in df.iterrows():
        if salary_col_high and salary_col:
            low_raw = pd.to_numeric(row[salary_col], errors="coerce")
            high_raw = pd.to_numeric(row[salary_col_high], errors="coerce")
            if pd.notna(low_raw) and pd.notna(high_raw) and low_raw > 0:
                val = (float(low_raw) + float(high_raw)) / 2
                total_salary += val
                salary_count += 1
                if val < 10000:
                    salary_bins["0-10K"] += 1
                elif val < 15000:
                    salary_bins["10-15K"] += 1
                elif val < 20000:
                    salary_bins["15-20K"] += 1
                elif val < 30000:
                    salary_bins["20-30K"] += 1
                elif val < 40000:
                    salary_bins["30-40K"] += 1
                else:
                    salary_bins["40K+"] += 1
        elif salary_col:
            val = _parse_salary(row[salary_col])
            if val > 0:
                total_salary += val
                salary_count += 1
                if val < 10000:
                    salary_bins["0-10K"] += 1
                elif val < 15000:
                    salary_bins["10-15K"] += 1
                elif val < 20000:
                    salary_bins["15-20K"] += 1
                elif val < 30000:
                    salary_bins["20-30K"] += 1
                elif val < 40000:
                    salary_bins["30-40K"] += 1
                else:
                    salary_bins["40K+"] += 1

        if edu_col:
            raw = str(row[edu_col])
            for label in edu_labels:
                if label in raw:
                    edu_counts[label] = edu_counts.get(label, 0) + 1
                    break
            else:
                edu_counts["不限"] = edu_counts.get("不限", 0) + 1

        if exp_col:
            raw = str(row[exp_col])
            for label in exp_labels:
                if label in raw:
                    exp_counts[label] = exp_counts.get(label, 0) + 1
                    break
            else:
                exp_counts["不限"] = exp_counts.get("不限", 0) + 1

    state = {
        "total_jobs": len(texts),
        "avg_salary": round(total_salary / salary_count) if salary_count else 0,
        "vocabulary_size": len(vocab),
        "vocab_top50": vocab[:50],
        "salary_distribution": {
            "labels": salary_labels,
            "data": [salary_bins[key] for key in salary_labels],
        },
        "education_distribution": {
            "labels": edu_labels,
            "data": [edu_counts.get(key, 0) for key in edu_labels],
        },
        "experience_distribution": {
            "labels": exp_labels,
            "data": [exp_counts.get(key, 0) for key in exp_labels],
        },
        "top_skills": [
            {"skill": s, "count": c} for s, c in tech_counter.most_common(20)
        ],
        "wordcloud": [
            {"word": s, "count": c} for s, c in tech_counter.most_common(100)
        ],
    }

    save_pipeline_state(state)
    return state


def save_pipeline_state(state: dict) -> None:
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO pipeline_state (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
        (_STATE_KEY, json.dumps(state, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def load_pipeline_state() -> dict:
    default = {
        "total_jobs": 0,
        "avg_salary": 0,
        "vocabulary_size": 0,
        "vocab_top50": [],
        "salary_distribution": {"labels": [], "data": []},
        "education_distribution": {"labels": [], "data": []},
        "experience_distribution": {"labels": [], "data": []},
        "top_skills": [],
        "wordcloud": [],
    }
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT value FROM pipeline_state WHERE key = ?", (_STATE_KEY,)
        ).fetchone()
    except Exception:
        conn.close()
        return default
    conn.close()
    if row:
        saved = json.loads(row["value"])
        return {**default, **saved}
    return default


def _find_column(df: pd.DataFrame, candidates: list[str], fallback: str) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _parse_salary(raw) -> float:
    s = str(raw).replace("K", "000").replace("k", "000")
    nums = re.findall(r"(\d+)\s*[－\-–—~到]\s*(\d+)", s)
    if nums:
        low = int(nums[0][0]) * 1000 if int(nums[0][0]) < 100 else int(nums[0][0])
        high = int(nums[0][1]) * 1000 if int(nums[0][1]) < 100 else int(nums[0][1])
        return (low + high) / 2
    single = re.findall(r"(\d+)(?:000|元|/月|月)?", s)
    if single:
        v = int(single[0])
        return v * 1000 if v < 100 else float(v)
    return 0.0
