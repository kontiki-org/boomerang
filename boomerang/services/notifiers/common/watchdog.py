import asyncio
import json
import logging
import os
import secrets
import time
from enum import StrEnum

from boomerang_contracts.notification.message import (
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
)

from boomerang.core.exceptions import AuthError, NotFoundError


class WatchdogState(StrEnum):
    UNSEEN = "unseen"
    UP = "up"
    DOWN = "down"


class WatchdogTransition(StrEnum):
    DOWN = "down"
    RECOVERED = "recovered"


class WatchdogEngine:
    def __init__(self, watchdogs, state_path, sweep_seconds, started_at):
        self._watchdogs = watchdogs
        self._state_path = state_path
        self._sweep_seconds = sweep_seconds
        self._started_at = started_at
        self._sweep_task = None
        self._records = {}
        self._load()

    def start(self, channel, send):
        self._sweep_task = asyncio.create_task(self._run(channel, send))

    async def stop(self):
        task = self._sweep_task
        if task is None:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._sweep_task = None

    async def _run(self, channel, send):
        logging.info("Starting sentinel sweep every %s seconds.", self._sweep_seconds)
        while True:
            try:
                await self.dispatch(channel, send)
                await asyncio.sleep(self._sweep_seconds)
            except asyncio.CancelledError:
                logging.info("Sentinel sweep cancelled.")
                break
            except Exception as exc:
                logging.error("Sentinel sweep failed: %s", exc)
                await asyncio.sleep(self._sweep_seconds)

    def known(self, name):
        return name in self._watchdogs

    def accept(self, headers, name, now):
        provided = _bearer_token(headers)
        expected = self._watchdogs[name]["token"]
        if provided is None or not secrets.compare_digest(provided, expected):
            raise AuthError()
        self._observe(name, now)

    async def dispatch(self, channel, send):
        for name, kind, endpoint_key in self._sweep(time.time()):
            request = _notification(channel, name, kind, endpoint_key)
            logging.info("Sending watchdog notification %s", request.message.title)
            await send(request)
            self._ack(name, kind)

    def _observe(self, name, now):
        record = self._record(name)
        if record["state"] is WatchdogState.DOWN:
            record["state"] = WatchdogState.UP
            record["pending"] = WatchdogTransition.RECOVERED
        else:
            record["state"] = WatchdogState.UP
        record["last_seen"] = now
        self._save()

    def _sweep(self, now):
        changed = False
        due = []
        for name, spec in self._watchdogs.items():
            record = self._record(name)
            if _timed_out(record, spec["timeout_seconds"], self._started_at, now):
                record["state"] = WatchdogState.DOWN
                record["pending"] = WatchdogTransition.DOWN
                changed = True
            if record["pending"]:
                due.append((name, record["pending"], spec["endpoint_key"]))
        if changed:
            self._save()
        return due

    def _ack(self, name, kind):
        record = self._records.get(name)
        if record is None or record["pending"] != kind:
            return
        record["pending"] = None
        self._save()

    def _record(self, name):
        record = self._records.get(name)
        if record is None:
            record = {
                "state": WatchdogState.UNSEEN,
                "last_seen": None,
                "pending": None,
            }
            self._records[name] = record
        return record

    def _load(self):
        if not os.path.isfile(self._state_path):
            return
        with open(self._state_path, encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise RuntimeError(f"Unreadable watchdog state file {self._state_path}")
        for name, raw in payload.items():
            if name not in self._watchdogs:
                continue
            self._records[name] = _record_from_file(self._state_path, raw)

    def _save(self):
        payload = {}
        for name in self._watchdogs:
            record = self._records.get(name)
            if record is None:
                continue
            if record["state"] is WatchdogState.UNSEEN and not record["pending"]:
                continue
            payload[name] = {
                "state": record["state"],
                "last_seen": record["last_seen"],
                "pending": record["pending"],
            }
        temporary = self._state_path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(temporary, self._state_path)


def load_watchdog(raw, endpoints):
    if raw is None:
        return None
    state_path = raw.get("state_path")
    if not state_path:
        raise RuntimeError(
            "Invalid app.sentinel configuration: sentinel state path is required."
        )
    sweep_seconds = raw.get("sweep_seconds", 1)
    watchdogs = {}
    for name, spec in raw.get("watchdogs", {}).items():
        watchdogs[name] = _watchdog_spec(spec, endpoints)
    if watchdogs:
        logging.info("Sentinel heartbeats enabled for %s", ", ".join(sorted(watchdogs)))
    return WatchdogEngine(watchdogs, state_path, sweep_seconds, time.time())


def accept_heartbeat(engine, headers, name):
    if engine is None or not engine.known(name):
        raise NotFoundError()
    engine.accept(headers, name, time.time())


def _watchdog_spec(spec, endpoints):
    endpoint_key = spec["endpoint_key"]
    if endpoints.get(endpoint_key) is None:
        raise RuntimeError(
            "Invalid app.sentinel configuration: "
            f"endpoint key {endpoint_key!r} is unknown."
        )
    return {
        "token": spec["token"],
        "timeout_seconds": spec["timeout_seconds"],
        "endpoint_key": endpoint_key,
    }


def _timed_out(record, timeout_seconds, started_at, now):
    if record["state"] is WatchdogState.UNSEEN:
        return now - started_at >= timeout_seconds
    if record["state"] is WatchdogState.UP:
        return now - record["last_seen"] >= timeout_seconds
    return False


def _notification(channel, name, kind, endpoint_key):
    label = "DOWN" if kind is WatchdogTransition.DOWN else "RECOVERED"
    return NotificationRequest(
        channel=channel,
        endpoint_key=endpoint_key,
        message=NotificationMessage(
            title=f"{label} {name}",
            body="",
            context=NotificationContext(kind="watchdog"),
        ),
    )


def _bearer_token(headers):
    header = headers.get("Authorization")
    if header is None:
        header = headers.get("authorization")
    if not isinstance(header, str) or not header.startswith("Bearer "):
        return None
    return header[len("Bearer ") :]


def _record_from_file(path, raw):
    if not isinstance(raw, dict):
        raise RuntimeError(f"Unreadable watchdog state file {path}")
    state = WatchdogState(raw["state"])
    pending = raw["pending"]
    if pending is not None:
        pending = WatchdogTransition(pending)
    last_seen = raw["last_seen"]
    if state is WatchdogState.UP and not isinstance(last_seen, (int, float)):
        raise RuntimeError(f"Unreadable watchdog state file {path}")
    return {"state": state, "last_seen": last_seen, "pending": pending}
