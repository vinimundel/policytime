from pathlib import Path

import pytest

from policytime.adapters.corpus import load_corpus
from policytime.bootstrap import build_runtime
from policytime.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def corpus():
    return load_corpus(ROOT / "corpus")


@pytest.fixture
def service():
    runtime = build_runtime(Settings(mode="demo", corpus_dir=ROOT / "corpus", _env_file=None))
    yield runtime.service
    runtime.close()
