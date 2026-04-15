import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from boomerang.services.subscription.http_models import CreateSubscriptionRequest
from boomerang.services.subscription.database.queries import (
    CREATE_SUBSCRIPTIONS_IDENTITY_INDEX,
    CREATE_SUBSCRIPTIONS_LOOKUP_INDEX,
    CREATE_SUBSCRIPTIONS_TABLE,
    CREATE_SUBSCRIPTIONS_USER_INDEX,
    CREATE_USERS_EMAIL_INDEX,
    CREATE_USERS_TABLE,
    INSERT_OR_IGNORE_SUBSCRIPTION,
    INSERT_OR_IGNORE_USER,
    SELECT_SUBSCRIPTIONS_BY_USER,
)


class Database:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    def setup(self):
        db_path = Path(self.sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection() as connection:
            connection.execute(CREATE_USERS_TABLE)
            connection.execute(CREATE_SUBSCRIPTIONS_TABLE)
            connection.execute(CREATE_USERS_EMAIL_INDEX)
            connection.execute(CREATE_SUBSCRIPTIONS_USER_INDEX)
            connection.execute(CREATE_SUBSCRIPTIONS_LOOKUP_INDEX)
            connection.execute(CREATE_SUBSCRIPTIONS_IDENTITY_INDEX)

    def ensure_user(self, email: str) -> str:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        user_id = self._build_user_id(email)
        with self._connection() as connection:
            connection.execute(INSERT_OR_IGNORE_USER, (user_id, email, None, now_iso, now_iso))
        return user_id

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
            rows = connection.execute(SELECT_SUBSCRIPTIONS_BY_USER, (user_id,)).fetchall()

        return [
            {
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
            for row in rows
        ]

    def _connection(self):
        connection = sqlite3.connect(self.sqlite_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

    @staticmethod
    def _build_user_id(email: str) -> str:
        digest = sha256(email.encode("utf-8")).hexdigest()
        return f"usr_{digest[:20]}"

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
