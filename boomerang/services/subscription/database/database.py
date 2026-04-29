import json
import logging
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from boomerang.core.contracts.subscription import CreateSubscriptionRequest
from boomerang.services.subscription.database.queries import (
    CREATE_CHANNEL_ENDPOINTS_TABLE,
    CREATE_CHANNEL_ENDPOINTS_UNIQUE_KEY,
    CREATE_CHANNEL_ENDPOINTS_USER_INDEX,
    CREATE_SUBSCRIPTIONS_IDENTITY_INDEX,
    CREATE_SUBSCRIPTIONS_LOOKUP_INDEX,
    CREATE_SUBSCRIPTIONS_TABLE,
    CREATE_SUBSCRIPTIONS_USER_INDEX,
    DELETE_SUBSCRIPTION,
    INSERT_OR_IGNORE_CHANNEL_ENDPOINT,
    INSERT_OR_IGNORE_SUBSCRIPTION,
    SELECT_CHANNEL_ENDPOINT_BY_KEY,
    SELECT_RECIPIENT_CANDIDATES_FOR_ALERT,
    SELECT_SUBSCRIPTION_BY_ID_AND_USER,
    SELECT_SUBSCRIPTIONS_BY_USER,
    UPDATE_SUBSCRIPTION,
)


class Database:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    def setup(self):
        db_path = Path(self.sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection() as connection:
            connection.execute(CREATE_SUBSCRIPTIONS_TABLE)
            connection.execute(CREATE_SUBSCRIPTIONS_USER_INDEX)
            connection.execute(CREATE_SUBSCRIPTIONS_LOOKUP_INDEX)
            connection.execute(CREATE_SUBSCRIPTIONS_IDENTITY_INDEX)
            connection.execute(CREATE_CHANNEL_ENDPOINTS_TABLE)
            connection.execute(CREATE_CHANNEL_ENDPOINTS_USER_INDEX)
            connection.execute(CREATE_CHANNEL_ENDPOINTS_UNIQUE_KEY)

    def create_subscriptions(
        self,
        user_id: str,
        payload: CreateSubscriptionRequest,
    ) -> tuple[list[dict], list[dict], list[dict]]:
        created = []
        skipped = []
        errors = []
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        delivery = payload.delivery.model_dump()
        policy = payload.policy.model_dump()
        delivery_json = json.dumps(delivery, separators=(",", ":"))
        policy_json = json.dumps(policy, separators=(",", ":"))

        with self._connection() as connection:
            for category in payload.selectors.categories:
                for event_type in payload.selectors.event_types:
                    for area in payload.selectors.areas:
                        try:
                            subscription_id = self._build_subscription_id(
                                user_id=user_id,
                                category=category,
                                event_type=event_type,
                                area_type=area.type,
                                area_value=area.value,
                                min_severity=payload.selectors.min_severity,
                            )
                            item = {
                                "subscription_id": subscription_id,
                                "user_id": user_id,
                                "category": category,
                                "event_type": event_type,
                                "area": {"type": area.type, "value": area.value},
                                "min_severity": payload.selectors.min_severity,
                                "delivery": delivery,
                                "policy": policy,
                                "status": "active",
                                "created_at": now_iso,
                                "updated_at": now_iso,
                            }
                            cursor = connection.execute(
                                INSERT_OR_IGNORE_SUBSCRIPTION,
                                (
                                    subscription_id,
                                    user_id,
                                    category,
                                    event_type,
                                    area.type,
                                    area.value,
                                    payload.selectors.min_severity,
                                    delivery_json,
                                    policy_json,
                                    now_iso,
                                    now_iso,
                                ),
                            )
                            if cursor.rowcount == 0:
                                skipped.append(item)
                            else:
                                created.append(item)
                        except Exception as exc:
                            logging.error("Error creating subscription.", exc_info=exc)
                            errors.append(
                                {
                                    "category": category,
                                    "event_type": event_type,
                                    "area": {"type": area.type, "value": area.value},
                                    "message": str(exc),
                                }
                            )

        return created, skipped, errors

    def list_subscriptions(self, user_id: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                SELECT_SUBSCRIPTIONS_BY_USER, (user_id,)
            ).fetchall()

        return [self._row_to_subscription_item(row) for row in rows]

    def update_subscription(
        self,
        user_id: str,
        subscription_id: str,
        min_severity: str | None,
        policy: dict | None,
        status: str | None,
    ) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                SELECT_SUBSCRIPTION_BY_ID_AND_USER,
                (subscription_id, user_id),
            ).fetchone()
            if row is None:
                return None

            current_min_severity = row["min_severity"]
            current_policy = json.loads(row["policy_json"])
            current_status = row["status"]

            next_min_severity = (
                min_severity if min_severity is not None else current_min_severity
            )
            next_policy = policy if policy is not None else current_policy
            next_status = status if status is not None else current_status
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            connection.execute(
                UPDATE_SUBSCRIPTION,
                (
                    next_min_severity,
                    json.dumps(next_policy, separators=(",", ":")),
                    next_status,
                    now_iso,
                    subscription_id,
                    user_id,
                ),
            )
            updated_row = connection.execute(
                SELECT_SUBSCRIPTION_BY_ID_AND_USER,
                (subscription_id, user_id),
            ).fetchone()
        if updated_row is None:
            return None
        return self._row_to_subscription_item(updated_row)

    def delete_subscription(self, user_id: str, subscription_id: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                DELETE_SUBSCRIPTION,
                (subscription_id, user_id),
            )
        return cursor.rowcount > 0

    def attach_channel_endpoint(
        self,
        user_id: str,
        channel: str,
        endpoint_key: str,
        is_default: bool,
    ) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        endpoint_id = self._build_endpoint_id(user_id, channel, endpoint_key)
        with self._connection() as connection:
            connection.execute(
                INSERT_OR_IGNORE_CHANNEL_ENDPOINT,
                (
                    endpoint_id,
                    user_id,
                    channel,
                    endpoint_key,
                    1 if is_default else 0,
                    now_iso,
                    now_iso,
                ),
            )
            row = connection.execute(
                SELECT_CHANNEL_ENDPOINT_BY_KEY,
                (user_id, channel, endpoint_key),
            ).fetchone()
        if row is None:
            raise RuntimeError("Channel endpoint persistence failed.")
        return dict(row)

    def get_recipients_for_alert(
        self,
        area_type: str,
        area_value: str,
        severity: str,
        category: str,
        event_type: str,
    ) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                SELECT_RECIPIENT_CANDIDATES_FOR_ALERT,
                (category, event_type, area_type, area_value),
            ).fetchall()

        recipients: dict[str, dict] = {}
        for row in rows:
            min_severity = row["min_severity"]
            if not self._severity_matches(min_severity=min_severity, severity=severity):
                continue

            user_id = row["user_id"]
            delivery = json.loads(row["delivery_json"])
            channel = row["channel"]
            endpoint_key = row["endpoint_key"]
            configured_channels = delivery.get("channels")
            if isinstance(configured_channels, list) and configured_channels:
                allowed_channels = {
                    item.strip().lower()
                    for item in configured_channels
                    if isinstance(item, str) and item.strip()
                }
                if channel not in allowed_channels:
                    continue

            entry = recipients.setdefault(
                user_id,
                {
                    "recipient_id": user_id,
                    "channels": set(),
                    "endpoint_keys": set(),
                },
            )
            entry["channels"].add(channel)
            entry["endpoint_keys"].add(endpoint_key)

        result = []
        for entry in recipients.values():
            result.append(
                {
                    "recipient_id": entry["recipient_id"],
                    "channels": sorted(entry["channels"]),
                    "endpoint_keys": sorted(entry["endpoint_keys"]),
                }
            )
        return sorted(result, key=lambda item: item["recipient_id"])

    def _connection(self):
        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    @staticmethod
    def _build_subscription_id(
        user_id: str,
        category: str,
        event_type: str,
        area_type: str,
        area_value: str,
        min_severity: str,
    ) -> str:
        canonical = (
            f"v1|{user_id}|{category}|{event_type}|"
            f"{area_type}|{area_value}|{min_severity}"
        )
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        return f"sub_{digest[:20]}"

    @staticmethod
    def _build_endpoint_id(user_id: str, channel: str, endpoint_key: str) -> str:
        canonical = f"v1|{user_id}|{channel}|{endpoint_key}"
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        return f"ep_{digest[:20]}"

    @staticmethod
    def _severity_matches(min_severity: str, severity: str) -> bool:
        order = {
            "low": 10,
            "moderate": 20,
            "severe": 30,
            "critical": 40,
        }
        min_rank = order.get(min_severity, -1)
        current_rank = order.get(severity, -1)
        if min_rank == -1 or current_rank == -1:
            return min_severity == severity
        return current_rank >= min_rank

    @staticmethod
    def _row_to_subscription_item(row: sqlite3.Row) -> dict:
        return {
            "subscription_id": row["subscription_id"],
            "user_id": row["user_id"],
            "category": row["category"],
            "event_type": row["event_type"],
            "area": {"type": row["area_type"], "value": row["area_value"]},
            "min_severity": row["min_severity"],
            "delivery": json.loads(row["delivery_json"]),
            "policy": json.loads(row["policy_json"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
