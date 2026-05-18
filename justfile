set := justfile_directory()

backend_args := " main:app --reload --port 8000 --app-dir " + justfile_directory() / "src/backend"
frontend_dir := justfile_directory() / "src/frontend"

# 安装依赖（CPU torch）
sync:
    cp uv-cpu.toml pyproject.toml && uv lock && uv sync

# 安装依赖（GPU torch）
sync-gpu:
    cp uv-gpu.toml pyproject.toml && uv lock && uv sync

# 启动后端
backend:
    uv run uvicorn{{backend_args}}

# 启动前端
frontend:
    cd {{frontend_dir}} && bun dev

# 同时启动前后端
start:
    uv run uvicorn{{backend_args}} &
    cd {{frontend_dir}} && bun dev

# 停止所有服务
stop:
    @fuser -k 8000/tcp 2>/dev/null || true
    @fuser -k 5173/tcp 2>/dev/null || true
    @sleep 0.5

# 运行全部测试
test:
    uv run python -m pytest src/backend/tests -v --tb=short

# 运行测试（跳过嵌入模型）
test-quick:
    uv run python -m pytest src/backend/tests -v --tb=short \
        --ignore=src/backend/tests/test_embedding.py \
        --ignore=src/backend/tests/test_embedding_classifier.py \
        --ignore=src/backend/tests/test_tsne.py \
        --ignore=src/backend/tests/test_vector_search.py

# 运行单个测试文件: just test-file classifier
test-file file:
    uv run python -m pytest src/backend/tests/test_{{file}}.py -v --tb=short

# 嵌入管道：BGE-M3 嵌入 + 向量索引
embed max_samples='5000':
    curl -s -X POST http://localhost:8000/api/data/embed \
        -H "Content-Type: application/json" \
        -d '{"max_samples": {{max_samples}}}' | uv run python -m json.tool

# t-SNE 降维: just tsne 3000 30
tsne sample_size='3000' perplexity='30':
    curl -s "http://localhost:8000/api/data/tsne?sample_size={{sample_size}}&perplexity={{perplexity}}" | uv run python -m json.tool

# t-SNE 强制重新计算
tsne-force sample_size='3000' perplexity='30':
    curl -s "http://localhost:8000/api/data/tsne?force=true&sample_size={{sample_size}}&perplexity={{perplexity}}" | uv run python -m json.tool

# 语义搜索
search q top_k='5':
    curl -s -X POST http://localhost:8000/api/data/vector-search \
        -H "Content-Type: application/json" \
        -d '{"query": "{{q}}", "top_k": {{top_k}}}' | uv run python -m json.tool

# AI 对话（含语义检索）
chat msg:
    curl -s -X POST http://localhost:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "{{msg}}", "use_semantic": true}'

# AI 对话（纯统计上下文）
chat-stats msg:
    curl -s -X POST http://localhost:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "{{msg}}", "use_semantic": false}'

# 查看对话上下文
context:
    curl -s http://localhost:8000/api/chat/context | uv run python -m json.tool

# 数据概览
summary:
    curl -s http://localhost:8000/api/data/summary | uv run python -m json.tool

# 全文统计
stats:
    curl -s http://localhost:8000/api/data/full-stats | uv run python -m json.tool

# 上传 CSV
upload file='data/上市公司招聘数据2026.csv':
    curl -s -X POST http://localhost:8000/api/data/upload \
        -F "file=@{{file}}" | uv run python -m json.tool

# 构建前端
build:
    cd {{frontend_dir}} && bun run build

# 清理构建产物
clean:
    rm -rf src/frontend/dist
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
