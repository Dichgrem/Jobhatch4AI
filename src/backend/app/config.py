import os

ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
LLM_MODEL = os.environ.get("LLM_MODEL", "ep-20250604061433-2k4xl")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "ep-20250611061140-4scq8")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
