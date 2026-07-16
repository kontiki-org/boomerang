import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from boomerang.testing import safe_unlink


def starter_root():
    return Path(__file__).resolve().parents[2]


def write_temp_config(config):
    fd, config_path = tempfile.mkstemp(suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)
    return config_path


def start_connector_subprocess(config):
    """Start the demo connector; returns (process, temp config path)."""
    config_path = write_temp_config(config)
    root = starter_root()
    src = str(root / "src")
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src + (os.pathsep + existing if existing else "")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "kontiki.runner.__main__",
            "connector.service.ConnectorService",
            "--config",
            config_path,
        ],
        cwd=str(root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    return proc, config_path


__all__ = [
    "safe_unlink",
    "starter_root",
    "start_connector_subprocess",
    "write_temp_config",
]
