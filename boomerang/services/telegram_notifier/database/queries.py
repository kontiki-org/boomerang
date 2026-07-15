"""
Telegram notifier service schema.

This DB stores only telegram endpoints keyed by the opaque user_id and endpoint_key.
"""

CREATE_TELEGRAM_ENDPOINTS_TABLE = """
CREATE TABLE IF NOT EXISTS telegram_endpoints (
    user_id TEXT NOT NULL,
    endpoint_key TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, endpoint_key)
);
"""

UPSERT_TELEGRAM_ENDPOINT = """
INSERT INTO telegram_endpoints (
    user_id,
    endpoint_key,
    chat_id,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(user_id, endpoint_key) DO UPDATE SET
    chat_id = excluded.chat_id,
    updated_at = excluded.updated_at;
"""

SELECT_TELEGRAM_ENDPOINT = """
SELECT
    user_id,
    endpoint_key,
    chat_id,
    created_at,
    updated_at
FROM telegram_endpoints
WHERE user_id = ? AND endpoint_key = ?;
"""

SELECT_TELEGRAM_ENDPOINTS_BY_USER = """
SELECT
    user_id,
    endpoint_key,
    chat_id,
    created_at,
    updated_at
FROM telegram_endpoints
WHERE user_id = ?
ORDER BY endpoint_key ASC;
"""

DELETE_TELEGRAM_ENDPOINT = """
DELETE FROM telegram_endpoints
WHERE user_id = ? AND endpoint_key = ?;
"""
