"""Which Behave suites this push or pull request must run.

BASE_SHA is the pull request base, or the commit before a push to main.
GITHUB_OUTPUT is set by Actions.
"""

import os
import re
import subprocess
import sys

EMPTY_SHA = "0000000000000000000000000000000000000000"

# Sentinel and the structured alert layout are shared by every notifier.
# Core, contracts, tooling, stack, and the image build can change any suite.
SUITES = (
    ("subscription", r"^boomerang/services/subscription/"),
    ("alert_engine", r"^boomerang/services/alert_engine/"),
    ("email", r"^boomerang/services/notifiers/email/"),
    ("telegram", r"^boomerang/services/notifiers/telegram/"),
    ("ntfy", r"^boomerang/services/notifiers/ntfy/"),
    ("notifiers_common", r"^boomerang/services/notifiers/common/"),
    (
        "shared",
        r"^(boomerang/core/|boomerang/testing/|boomerang/__init__\.py|"
        r"packages/boomerang-contracts/|pyproject\.toml$|poetry\.lock$|"
        r"Makefile$|stack/|docker-compose|Dockerfile$|docker/)",
    ),
)


def changed_files(base):
    # A brand-new branch, or a push with no parent, has nothing to diff.
    if not base or base == EMPTY_SHA:
        return None
    exists = subprocess.run(
        ["git", "cat-file", "-e", base + "^{commit}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if exists.returncode != 0:
        return None
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return diff.stdout.splitlines()


def main():
    files = changed_files(os.environ.get("BASE_SHA", ""))
    output = os.environ["GITHUB_OUTPUT"]
    with open(output, "a", encoding="utf-8") as handle:
        for name, pattern in SUITES:
            # None means every suite runs.
            hit = files is None or any(re.search(pattern, path) for path in files)
            handle.write(f"{name}={'true' if hit else 'false'}\n")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
