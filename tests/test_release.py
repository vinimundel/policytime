"""A failed candidate must restore policy authority as well as the image."""

import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location("release", Path("deploy/release.py"))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_failed_candidate_restores_corpus_before_previous_image(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"image": "ghcr.io/vinimundel/policytime:v0.0.1"}))
    calls = []

    def run(*args, image):
        calls.append((args, image))

    with (
        patch.object(release, "STATE", state),
        patch.object(release, "run", run),
        patch.object(release, "corpus_version", return_value="a" * 64),
        patch.object(release, "readiness", side_effect=subprocess.CalledProcessError(1, "ready")),
        patch("sys.argv", ["release.py", "ghcr.io/vinimundel/policytime:v0.1.0"]),
        pytest.raises(subprocess.CalledProcessError),
    ):
        release.main()
    assert "UPDATE active_corpus" in calls[-2][0][-1]
    assert calls[-1][1] == "ghcr.io/vinimundel/policytime:v0.0.1"
    assert json.loads(state.read_text())["image"].endswith(":v0.0.1")


def test_restore_rejects_invalid_fingerprint():
    with pytest.raises(ValueError):
        release.restore_corpus("'; DROP TABLE corpora;", "unused")
