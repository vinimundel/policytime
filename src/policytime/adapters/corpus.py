"""Load explicitly authored Markdown policy clauses; never infer their authority."""

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from policytime.domain.models import Corpus, PolicyDocument
from policytime.domain.resolution import validate_corpus


def load_corpus(directory: Path) -> Corpus:
    paths = sorted(directory.glob("*.md"))
    if not paths:
        raise ValueError(f"No policy Markdown files in {directory}")
    documents = tuple(_load_document(path) for path in paths)
    canonical = json.dumps(
        [document.model_dump(mode="json") for document in documents],
        sort_keys=True,
    )
    corpus = Corpus(version=hashlib.sha256(canonical.encode()).hexdigest(), documents=documents)
    validate_corpus(corpus)
    return corpus


def _load_document(path: Path) -> PolicyDocument:
    content = path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"Expected YAML front matter in {path.name}")
    metadata: Any = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected metadata object in {path.name}")
    passages = _clause_passages(parts[2])
    for clause in metadata.get("clauses", []):
        identifier = clause["id"]
        if identifier not in passages:
            raise ValueError(f"Missing clause heading {identifier} in {path.name}")
        clause["text"] = passages.pop(identifier)
    if passages:
        raise ValueError(f"Unregistered clause headings in {path.name}")
    return PolicyDocument.model_validate(metadata)


def _clause_passages(body: str) -> dict[str, str]:
    passages: dict[str, str] = {}
    for section in body.split("\n## ")[1:]:
        heading, _, text = section.partition("\n")
        if heading.strip() in passages:
            raise ValueError("Duplicate clause heading.")
        passages[heading.strip()] = text.strip()
    return passages


class FileCorpusRepository:
    def __init__(self, directory: Path) -> None:
        self._corpus = load_corpus(directory)

    def snapshot(self) -> Corpus:
        return self._corpus
