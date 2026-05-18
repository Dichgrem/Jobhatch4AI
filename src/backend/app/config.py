import os

from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("ARK_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
