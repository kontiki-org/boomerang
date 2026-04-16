import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from boomerang.services.identity.database.queries import (
    CREATE_AUTH_CODES_EMAIL_INDEX,
    CREATE_AUTH_CODES_TABLE,
    CREATE_SESSIONS_TABLE,
    CREATE_SESSIONS_USER_INDEX,
    DELETE_EXPIRED_AUTH_CODES,
    DELETE_EXPIRED_SESSIONS,
    INSERT_AUTH_CODE,
    INSERT_SESSION,
    MARK_AUTH_CODE_USED,
    SELECT_AUTH_CODE,
    SELECT_SESSION,
)


class Database:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = sqlite_path

    def setup(self) -> None:
        db_path = Path(self.sqlite_path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connection() as connection:
            connection.execute(CREATE_AUTH_CODES_TABLE)
            connection.execute(CREATE_AUTH_CODES_EMAIL_INDEX)
            connection.execute(CREATE_SESSIONS_TABLE)
            connection.execute(CREATE_SESSIONS_USER_INDEX)

    def insert_auth_code(self, code: str, email: str, expires_at: str) -> None:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connection() as connection:
            connection.execute(INSERT_AUTH_CODE, (code, email, expires_at, 0, now_iso))

    def get_auth_code(self, code: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(SELECT_AUTH_CODE, (code,)).fetchone()
        if not row:
            return None
        return {"code": row[0], "email": row[1], "expires_at": row[2], "used": row[3]}

    def mark_auth_code_used(self, code: str) -> None:
        with self._connection() as connection:
            connection.execute(MARK_AUTH_CODE_USED, (code,))

    def insert_session(
        self, access_token: str, user_id: str, email: str, expires_at: str
    ):
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connection() as connection:
            connection.execute(
                INSERT_SESSION,
                (access_token, user_id, email, expires_at, now_iso),
            )

    def get_session(self, access_token: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(SELECT_SESSION, (access_token,)).fetchone()
        if not row:
            return None
        return {
            "access_token": row[0],
            "user_id": row[1],
            "email": row[2],
            "expires_at": row[3],
        }

    def cleanup_expired(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with self._connection() as connection:
            connection.execute(DELETE_EXPIRED_AUTH_CODES, (now_iso,))
            connection.execute(DELETE_EXPIRED_SESSIONS, (now_iso,))

    @staticmethod
    def build_user_id(email: str) -> str:
        digest = sha256(email.encode("utf-8")).hexdigest()
        return f"usr_{digest[:20]}"

    def _connection(self):
        connection = sqlite3.connect(self.sqlite_path)
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection
