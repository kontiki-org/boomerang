import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from boomerang.services.sms_notifier.database import queries


class Database:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    def setup(self) -> None:
        db_path = Path(self.sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection() as connection:
            connection.execute(queries.CREATE_SMS_ENDPOINTS_TABLE)

    def upsert_sms_endpoint(
        self, user_id: str, endpoint_key: str, phone_number: str
    ) -> dict:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connection() as connection:
            connection.execute(
                queries.UPSERT_SMS_ENDPOINT,
                (user_id, endpoint_key, phone_number, now_iso, now_iso),
            )
            row = connection.execute(
                queries.SELECT_SMS_ENDPOINT, (user_id, endpoint_key)
            ).fetchone()

        return {
            "user_id": row[0],
            "endpoint_key": row[1],
            "phone_number": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }

    def get_sms_endpoint(self, user_id: str, endpoint_key: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                queries.SELECT_SMS_ENDPOINT, (user_id, endpoint_key)
            ).fetchone()
        if not row:
            return None
        return {
            "user_id": row[0],
            "endpoint_key": row[1],
            "phone_number": row[2],
            "created_at": row[3],
            "updated_at": row[4],
        }

    def list_sms_endpoints(self, user_id: str) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                queries.SELECT_SMS_ENDPOINTS_BY_USER, (user_id,)
            ).fetchall()
        endpoints = []
        for row in rows:
            endpoints.append(
                {
                    "user_id": row[0],
                    "endpoint_key": row[1],
                    "phone_number": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                }
            )
        return endpoints

    def delete_sms_endpoint(self, user_id: str, endpoint_key: str) -> bool:
        with self._connection() as connection:
            cursor = connection.execute(
                queries.DELETE_SMS_ENDPOINT, (user_id, endpoint_key)
            )
            return cursor.rowcount > 0

    def _connection(self):
        connection = sqlite3.connect(self.sqlite_path)
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection

