set := justfile_directory()

run_backend := "python3 -m fastapi dev src/backend/main.py --port 8000"
frontend_dir := justfile_directory() / "src/frontend"

# 安装依赖
install:
    cd {{frontend_dir}} && bun install

# 启动后端
backend:
    {{run_backend}}

# 启动前端
frontend:
    cd {{frontend_dir}} && bun dev

# 同时启动前后端
start:
    {{run_backend}} &
    cd {{frontend_dir}} && bun dev

# 停止所有服务
stop:
    @fuser -k 8000/tcp 2>/dev/null || true
    @fuser -k 5173/tcp 2>/dev/null || true
    @sleep 0.5

# 构建前端
build:
    cd {{frontend_dir}} && bun run build

# 格式化所有代码
fmt:
    ruff format src/backend
    cd {{frontend_dir}} && biome format --write .
    taplo format *.toml uv-cpu.toml uv-gpu.toml

# 代码检查与自动修复
lint:
    ruff check --fix src/backend
    cd {{frontend_dir}} && biome check --write .
    deadnix -f . || true
    taplo lint *.toml uv-cpu.toml uv-gpu.toml
    rumdl fmt README.md
    rumdl check README.md

# 同时格式化和检查
check: fmt lint

# 清理构建产物
clean:
    rm -rf src/frontend/dist
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
