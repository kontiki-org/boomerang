import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from boomerang.core.service_contracts.subscription import (
    CreateSubscriptionRequest,
    CriteriaExpression,
    EndpointRef,
    RuleDefinition,
    UpdateSubscriptionRequest,
)
from boomerang.services.subscription.database.queries import (
    CREATE_SUBSCRIPTIONS_IDENTITY_INDEX,
    CREATE_SUBSCRIPTIONS_LOOKUP_INDEX,
    CREATE_SUBSCRIPTIONS_TABLE,
    CREATE_SUBSCRIPTIONS_USER_INDEX,
    DELETE_SUBSCRIPTION,
    INSERT_OR_IGNORE_SUBSCRIPTION,
    SELECT_RECIPIENT_CANDIDATES_FOR_ALERT,
    SELECT_SUBSCRIPTION_BY_ID_AND_USER,
    SELECT_SUBSCRIPTIONS_BY_USER,
    UPDATE_SUBSCRIPTION,
)
from boomerang.services.subscription.subscription_resolution import (
    build_facts_from_alert,
    criteria_matches,
    sort_recipients,
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

    def create_subscriptions(
        self,
        user_id: str,
        payload: CreateSubscriptionRequest,
    ) -> tuple[list[dict], list[dict], list[dict]]:
        created: list[dict] = []
        skipped: list[dict] = []
        errors: list[dict] = []
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        rule = payload.subscription.rule
        criteria_json = json.dumps(rule.criteria.model_dump(), separators=(",", ":"))
        endpoints_json = json.dumps(
            [endpoint.model_dump() for endpoint in payload.subscription.endpoints],
            separators=(",", ":"),
        )
        subscription_id = self._build_subscription_id(
            user_id=user_id,
            category=rule.category,
            event_type=rule.event_type,
            criteria_json=criteria_json,
            endpoints_json=endpoints_json,
        )
        item = {
            "subscription_id": subscription_id,
            "user_id": user_id,
            "subscription": {
                "rule": rule.model_dump(),
                "endpoints": [
                    endpoint.model_dump() for endpoint in payload.subscription.endpoints
                ],
            },
            "status": "active",
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        with self._connection() as connection:
            try:
                cursor = connection.execute(
                    INSERT_OR_IGNORE_SUBSCRIPTION,
                    (
                        subscription_id,
                        user_id,
                        rule.category,
                        rule.event_type,
                        criteria_json,
                        endpoints_json,
                        now_iso,
                        now_iso,
                    ),
                )
                if cursor.rowcount == 0:
                    skipped.append(item)
                else:
                    created.append(item)
            except Exception as exc:
                errors.append({"subscription_id": subscription_id, "message": str(exc)})

        return created, skipped, errors

    def get_subscriptions(self, user_id: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                SELECT_SUBSCRIPTIONS_BY_USER, (user_id,)
            ).fetchall()

        return [self._row_to_subscription_item(row) for row in rows]

    def update_subscription(
        self,
        user_id: str,
        subscription_id: str,
        body: UpdateSubscriptionRequest,
    ) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                SELECT_SUBSCRIPTION_BY_ID_AND_USER,
                (subscription_id, user_id),
            ).fetchone()
            if row is None:
                return None

            current_category = row["category"]
            current_event_type = row["event_type"]
            current_criteria = row["criteria_json"]
            current_endpoints = row["endpoints_json"]
            current_status = row["status"]

            next_category = (
                body.rule.category if body.rule is not None else current_category
            )
            next_event_type = (
                body.rule.event_type if body.rule is not None else current_event_type
            )
            next_criteria = (
                json.dumps(body.rule.criteria.model_dump(), separators=(",", ":"))
                if body.rule is not None
                else current_criteria
            )
            next_endpoints = (
                json.dumps(
                    [endpoint.model_dump() for endpoint in body.endpoints],
                    separators=(",", ":"),
                )
                if body.endpoints is not None
                else current_endpoints
            )
            next_status = body.status if body.status is not None else current_status
            now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            connection.execute(
                UPDATE_SUBSCRIPTION,
                (
                    next_category,
                    next_event_type,
                    next_criteria,
                    next_endpoints,
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

    def get_recipients_for_alert(
        self,
        alert: dict | None = None,
        area_type: str | None = None,
        area_value: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        if alert is None:
            alert = {
                "area_type": area_type,
                "area_value": area_value,
                "severity": severity,
                "category": category,
                "event_type": event_type,
                "areas": (
                    [{"type": area_type, "value": area_value}]
                    if area_type and area_value
                    else []
                ),
            }
        category, event_type, facts = build_facts_from_alert(alert)
        if not category or not event_type:
            return []
        with self._connection() as connection:
            rows = connection.execute(
                SELECT_RECIPIENT_CANDIDATES_FOR_ALERT,
                (category, event_type),
            ).fetchall()

        targets: list[dict] = []
        for row in rows:
            criteria = json.loads(row["criteria_json"])
            if not criteria_matches(criteria, facts):
                continue

            user_id = row["user_id"]
            endpoints = json.loads(row["endpoints_json"])
            for endpoint in endpoints:
                kind = str(endpoint.get("kind", "")).strip().lower()
                endpoint_key = str(endpoint.get("endpoint_key", "")).strip()
                if not kind or not endpoint_key:
                    continue
                targets.append(
                    {
                        "recipient_id": user_id,
                        "channel": kind,
                        "endpoint_key": endpoint_key,
                    }
                )
        return sort_recipients(targets)

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
        criteria_json: str,
        endpoints_json: str,
    ) -> str:
        canonical = (
            f"v2|{user_id}|{category}|{event_type}|{criteria_json}|{endpoints_json}"
        )
        digest = sha256(canonical.encode("utf-8")).hexdigest()
        return f"sub_{digest[:20]}"

    @staticmethod
    def _row_to_subscription_item(row: sqlite3.Row) -> dict:
        criteria = CriteriaExpression.model_validate(json.loads(row["criteria_json"]))
        endpoints = [
            EndpointRef.model_validate(item).model_dump()
            for item in json.loads(row["endpoints_json"])
        ]
        rule = RuleDefinition(
            category=row["category"],
            event_type=row["event_type"],
            criteria=criteria,
        )
        return {
            "subscription_id": row["subscription_id"],
            "user_id": row["user_id"],
            "subscription": {
                "rule": rule.model_dump(),
                "endpoints": endpoints,
            },
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
