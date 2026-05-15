from collections import Counter
from pathlib import Path

import jieba
import numpy as np
import pandas as pd


def load_csv(path: str | Path, text_column: str = "keyword") -> pd.DataFrame:
    encodings = ["utf-8", "gb18030", "gbk", "gb2312"]
    path = Path(path)
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        raise ValueError(f"无法读取文件: {path}")
    df.dropna(subset=[text_column], inplace=True)
    return df


def tokenize(text: str) -> list[str]:
    words = jieba.lcut(text)
    return [w.strip().lower() for w in words if len(w.strip()) > 1]


def build_vocab(
    token_lists: list[list[str]], min_freq: int = 5, max_size: int = 5000
) -> list[str]:
    counter: Counter[str] = Counter()
    for tokens in token_lists:
        counter.update(tokens)
    return [
        word for word, _ in counter.most_common(max_size) if counter[word] >= min_freq
    ]


def text_to_bow(tokens: list[str], vocab: list[str]) -> np.ndarray:
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    vec = np.zeros(len(vocab), dtype=np.float32)
    for token in tokens:
        if token in word_to_idx:
            vec[word_to_idx[token]] += 1
    return vec


def extract_tech_terms(tokens: list[str], tech_list: list[str]) -> list[str]:
    tech_set = set(tech_list)
    return [t for t in tokens if t in tech_set]


TECH_TERMS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "go",
    "rust",
    "c++",
    "c#",
    "php",
    "ruby",
    "swift",
    "kotlin",
    "scala",
    "r",
    "matlab",
    "shell",
    "sql",
    "html",
    "css",
    "sass",
    "less",
    "spring",
    "springboot",
    "mybatis",
    "hibernate",
    "django",
    "flask",
    "fastapi",
    "tornado",
    "express",
    "koa",
    "vue",
    "react",
    "angular",
    "jquery",
    "bootstrap",
    "nextjs",
    "nuxt",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "elasticsearch",
    "oracle",
    "sqlserver",
    "sqlite",
    "cassandra",
    "neo4j",
    "hbase",
    "hive",
    "kafka",
    "rabbitmq",
    "rocketmq",
    "activemq",
    "zeromq",
    "pulsar",
    "docker",
    "kubernetes",
    "jenkins",
    "gitlab",
    "github",
    "ansible",
    "terraform",
    "prometheus",
    "grafana",
    "elk",
    "nginx",
    "apache",
    "tomcat",
    "haproxy",
    "envoy",
    "spark",
    "hadoop",
    "flink",
    "storm",
    "airflow",
    "dbt",
    "tensorflow",
    "pytorch",
    "keras",
    "scikit-learn",
    "pandas",
    "numpy",
    "opencv",
    "nlp",
    "transformers",
    "langchain",
    "llm",
    "rag",
    "linux",
    "unix",
    "tcp/ip",
    "http",
    "grpc",
    "websocket",
    "restful",
    "graphql",
    "microservices",
    "soa",
    "ddd",
    "git",
    "svn",
    "maven",
    "gradle",
    "npm",
    "yarn",
    "pip",
    "junit",
    "selenium",
    "pytest",
    "unittest",
    "jmeter",
    "aws",
    "azure",
    "gcp",
    "aliyun",
    "tencentcloud",
    "agile",
    "scrum",
    "devops",
    "cicd",
    "mlops",
]
