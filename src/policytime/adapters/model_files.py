"""Explicit downloads pin upstream commits; runtime model loading stays offline."""

import json
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

from policytime.adapters.retrieval import EMBEDDING_MODEL, RERANKER_MODEL


def download_models(destination: Path) -> dict[str, dict[str, str]]:
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "manifest.json"
    lock_path = manifest_path if manifest_path.exists() else Path("models.lock.json")
    previous = json.loads(lock_path.read_text()) if lock_path.exists() else {}
    manifest: dict[str, dict[str, str]] = {}
    for name, repository in (("embedding", EMBEDDING_MODEL), ("reranker", RERANKER_MODEL)):
        revision = previous.get(name, {}).get("revision") or HfApi().model_info(repository).sha
        if not revision:
            raise RuntimeError(f"Could not resolve an immutable revision for {repository}")
        snapshot_download(
            repository,
            revision=revision,
            local_dir=destination / name,
            allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.md", "LICENSE"],
            ignore_patterns=["onnx/*", "openvino/*", "*.bin", "*.h5", "*.ot"],
        )
        manifest[name] = {"repository": repository, "revision": revision}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
