import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import database as db_module


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        pass
    tmp_path = Path(f.name)
    original = db_module.DB_PATH
    db_module.DB_PATH = tmp_path
    db_module.init_db()
    yield tmp_path
    db_module.DB_PATH = original
    tmp_path.unlink(missing_ok=True)
