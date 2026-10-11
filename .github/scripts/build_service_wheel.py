"""Build dist/boomerang-<service>-<version>.whl.

SERVICE and VERSION name the distribution. The wheel installs the boomerang
tree and exposes one command, boomerang-$SERVICE.

SOURCE_REF, when set, is the git tag service/version. The tree and
pyproject.toml are read from that tag, so an image already published can
get a matching wheel without moving the tag. Unset means the working tree.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SERVICE_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

READMES = {
    "subscription": "boomerang/services/subscription/README.md",
    "alert-engine": "boomerang/services/alert_engine/README.md",
    "email-notifier": "boomerang/services/notifiers/email/README.md",
    "telegram-notifier": "boomerang/services/notifiers/telegram/README.md",
    "ntfy-notifier": "boomerang/services/notifiers/ntfy/README.md",
}

DESCRIPTIONS = {
    "subscription": "Boomerang subscription service.",
    "alert-engine": "Boomerang alert engine.",
    "email-notifier": "Boomerang email notifier.",
    "telegram-notifier": "Boomerang Telegram notifier.",
    "ntfy-notifier": "Boomerang ntfy notifier.",
}


def quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def fail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def load_poetry(ref):
    if ref:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:pyproject.toml"], cwd=ROOT
        )
    else:
        raw = (ROOT / "pyproject.toml").read_bytes()
    return tomllib.loads(raw.decode())["tool"]["poetry"]


def pyproject_text(service, version, poetry):
    command = f"boomerang-{service}"
    entry = poetry["scripts"][command]
    lines = [
        "[build-system]",
        'requires = ["poetry-core"]',
        'build-backend = "poetry.core.masonry.api"',
        "",
        "[tool.poetry]",
        f"name = {quote('boomerang-' + service)}",
        f"version = {quote(version)}",
        f"description = {quote(DESCRIPTIONS[service])}",
        "authors = [",
    ]
    for author in poetry["authors"]:
        lines.append(f"    {quote(author)},")
    lines.extend(
        [
            "]",
            'readme = "README.md"',
            'license = "Apache-2.0"',
            f"homepage = {quote(poetry['homepage'])}",
            f"repository = {quote(poetry['repository'])}",
            'packages = [{ include = "boomerang" }]',
            'exclude = ["boomerang/**/tests", "boomerang/**/tests/**"]',
            "classifiers = [",
        ]
    )
    for item in poetry["classifiers"]:
        lines.append(f"    {quote(item)},")
    lines.extend(
        [
            "]",
            "",
            "[tool.poetry.dependencies]",
        ]
    )
    for key, value in poetry["dependencies"].items():
        if not isinstance(value, str):
            fail(f"Unsupported dependency table for {key}.")
        lines.append(f"{key} = {quote(value)}")
    lines.append("")
    lines.append("[tool.poetry.scripts]")
    lines.append(f"{command} = {quote(entry)}")
    lines.append("")
    return "\n".join(lines)


def fill(dest, ref, readme_path):
    if ref:
        archive = subprocess.check_output(
            ["git", "archive", ref, "boomerang", "LICENSE"], cwd=ROOT
        )
        subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
        readme = subprocess.check_output(
            ["git", "show", f"{ref}:{readme_path}"], cwd=ROOT
        )
        (dest / "README.md").write_bytes(readme)
        return
    shutil.copytree(
        ROOT / "boomerang",
        dest / "boomerang",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    shutil.copy(ROOT / "LICENSE", dest / "LICENSE")
    shutil.copy(ROOT / readme_path, dest / "README.md")


def main():
    service = os.environ.get("SERVICE", "")
    version = os.environ.get("VERSION", "")
    ref = os.environ.get("SOURCE_REF", "")
    if not SERVICE_RE.match(service) or service not in READMES:
        fail(f"Unknown service: {service}")
    if not VERSION_RE.match(version):
        fail(f"Version must be x.y.z, got: {version}")
    if ref and ref != f"{service}/{version}":
        fail(f"SOURCE_REF must be {service}/{version}, got: {ref}")
    poetry = load_poetry(ref)
    command = f"boomerang-{service}"
    if command not in poetry["scripts"]:
        fail(f"No {command} command in pyproject.toml")
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        fill(dest, ref, READMES[service])
        (dest / "pyproject.toml").write_text(
            pyproject_text(service, version, poetry), encoding="utf-8"
        )
        subprocess.check_call(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist)],
            cwd=dest,
        )


if __name__ == "__main__":
    try:
        import build  # noqa: F401
    except ImportError:
        fail("pip install build")
    main()
