import subprocess
import sys
import time
from pathlib import Path

_INTEGRATION_DIR = Path(__file__).resolve().parent
if str(_INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(_INTEGRATION_DIR))

_STARTER_SRC = str(_INTEGRATION_DIR.parents[1] / "src")
if _STARTER_SRC not in sys.path:
    sys.path.insert(0, _STARTER_SRC)

from kontiki.testing import MockServiceManager, MockServiceRunner
from mocks import AlertNormalizedEventCatcher
from utils import safe_unlink


def before_all(context):
    time.sleep(1)
    context.connector_process = None
    context.connector_config_path = None

    default_config = {"kontiki": {"amqp": {"url": "amqp://guest:guest@localhost/"}}}
    context.manager = MockServiceManager(
        log_file="/tmp/boomerang-alert-connector-starter.log"
    )
    context.manager.add(AlertNormalizedEventCatcher, default_config)
    context.runner = MockServiceRunner(context.manager)
    context.runner.start()
    context.runner.ready_event.wait(timeout=10)


def before_scenario(context, scenario):
    _ = scenario
    context.manager.clean_events("alert-normalized-event-catcher")


def after_scenario(context, scenario):
    _ = scenario
    if context.connector_process is not None:
        context.connector_process.terminate()
        try:
            context.connector_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            context.connector_process.kill()
            context.connector_process.wait(timeout=5)
        context.connector_process = None

    safe_unlink(context.connector_config_path)
    context.connector_config_path = None
    context.manager.clean_events("alert-normalized-event-catcher")


def after_all(context):
    context.runner.stop()
