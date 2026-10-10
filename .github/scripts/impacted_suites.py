"""Which Behave suites this push or pull request must run.

BASE_SHA is the pull request base, or the commit before a push to main.
GITHUB_OUTPUT is set by Actions.
"""

import os
import subprocess
import sys

EMPTY_SHA = "0000000000000000000000000000000000000000"
SUITES_FILE = os.path.join(os.path.dirname(__file__), "impacted-suites.txt")


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


def load_suites():
    suites = {}
    with open(SUITES_FILE, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, prefix = line.split(None, 1)
            suites.setdefault(name, []).append(prefix)
    return suites


def main():
    files = changed_files(os.environ.get("BASE_SHA", ""))
    output = os.environ["GITHUB_OUTPUT"]
    with open(output, "a", encoding="utf-8") as handle:
        for name, prefixes in load_suites().items():
            # None means every suite runs.
            hit = files is None or any(
                path.startswith(prefix) for path in files for prefix in prefixes
            )
            handle.write(f"{name}={'true' if hit else 'false'}\n")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
