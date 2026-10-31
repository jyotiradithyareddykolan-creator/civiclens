import copy
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Deterministic, offline, key-less defaults. Set BEFORE importing the app.
FIXTURES = Path(__file__).resolve().parent / "fixtures"
REAL_DATA = Path(__file__).resolve().parent.parent / "data" / "schemes.json"
# The engine tests (AC-01..12, test cases 1-10) run on SYNTHETIC fixtures because they need contrived situations
# (conflicting circulars, injection text, two versions). test_real_data.py runs against the shipped real data.
os.environ["CIVICLENS_DATA_PATH"] = str(FIXTURES / "demo_schemes.json")
os.environ["CIVICLENS_TODAY"] = "2026-10-30"
os.environ["CIVICLENS_LIVE_FETCH"] = "0"
os.environ["CIVICLENS_RATE_LIMIT_PER_MINUTE"] = "100000"
os.environ.pop("ANTHROPIC_API_KEY", None)
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("CIVICLENS_LLM_PROVIDER", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import llm  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.store import get_store, load_data, reload_store  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_state():
    llm.set_backend(None)
    reload_store()
    yield
    llm.set_backend(None)
    reload_store()


@pytest.fixture()
def raw_data():
    return copy.deepcopy(load_data(get_settings().data_path))


@pytest.fixture()
def store():
    return get_store()


@pytest.fixture()
def client():
    return TestClient(create_app(), raise_server_exceptions=False)


# ---- reusable profiles
STUDENT = {"age": 20, "state": "delhi", "annual_income": 250000, "occupation": "student", "education_level": "undergraduate"}
