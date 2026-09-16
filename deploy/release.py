"""Deploy a tagged image, then roll back the application if readiness fails.

Run on the VM from the repository root. Schema migrations must remain backward
compatible; automatic rollback never attempts a destructive schema downgrade.
"""

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path

COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    "deploy/production.env",
    "-f",
    "compose.production.yaml",
]
STATE = Path("deploy/release-state.json")


def run(*arguments: str, image: str) -> None:
    subprocess.run(
        [*COMPOSE, *arguments], env={**os.environ, "POLICYTIME_IMAGE": image}, check=True
    )


def readiness(image: str) -> None:
    run(
        "exec",
        "-T",
        "app",
        "python",
        "-c",
        (
            "import urllib.request; "
            "urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=5)"
        ),
        image=image,
    )


def corpus_version(image: str) -> str | None:
    result = subprocess.run(
        [
            *COMPOSE,
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            "postgres",
            "-d",
            "policytime",
            "-Atc",
            "SELECT version FROM active_corpus WHERE id = 1",
        ],
        env={**os.environ, "POLICYTIME_IMAGE": image},
        check=True,
        capture_output=True,
        text=True,
    )
    version = result.stdout.strip()
    if version and not re.fullmatch(r"[a-f0-9]{64}", version):
        raise RuntimeError("Invalid active corpus fingerprint")
    return version or None


def restore_corpus(version: str | None, image: str) -> None:
    if version is None:
        return
    if not re.fullmatch(r"[a-f0-9]{64}", version):
        raise ValueError("Invalid corpus fingerprint")
    run(
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        "postgres",
        "-d",
        "policytime",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        f"UPDATE active_corpus SET version = '{version}' WHERE id = 1",
        image=image,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="ghcr.io/OWNER/policytime:vMAJOR.MINOR.PATCH")
    args = parser.parse_args()
    image = args.image
    if not re.fullmatch(r"ghcr\.io/[a-z0-9_.-]+/policytime:v\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", image):
        raise SystemExit("Use an immutable version tag, not latest.")
    previous = json.loads(STATE.read_text())["image"] if STATE.exists() else None
    run("pull", "app", image=image)
    run("up", "-d", "--wait", "db", image=image)
    run("run", "--rm", "app", "alembic", "upgrade", "head", image=image)
    previous_corpus = corpus_version(image)
    run("run", "--rm", "app", "policytime", "ingest", image=image)
    try:
        run("up", "-d", "--wait", "--wait-timeout", "180", "app", "caddy", image=image)
        readiness(image)
    except subprocess.CalledProcessError:
        restore_corpus(previous_corpus, image)
        if previous:
            run("up", "-d", "--wait", "--wait-timeout", "180", "app", image=previous)
        raise
    STATE.write_text(
        json.dumps(
            {
                "image": image,
                "previous_image": previous,
                "previous_corpus": previous_corpus,
                "deployed_at_unix": int(time.time()),
            },
            indent=2,
        )
        + "\n"
    )
    print("Application is ready. Update POLICYTIME_IMAGE in production.env to", image)


if __name__ == "__main__":
    main()
