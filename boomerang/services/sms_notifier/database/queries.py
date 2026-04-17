"""
SMS notifier service schema.

This DB stores sms endpoints keyed by the opaque user_id and endpoint_key.
"""

CREATE_SMS_ENDPOINTS_TABLE = """
CREATE TABLE IF NOT EXISTS sms_endpoints (
    user_id TEXT NOT NULL,
    endpoint_key TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, endpoint_key)
);
"""

UPSERT_SMS_ENDPOINT = """
INSERT INTO sms_endpoints (
    user_id,
    endpoint_key,
    phone_number,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(user_id, endpoint_key) DO UPDATE SET
    phone_number = excluded.phone_number,
    updated_at = excluded.updated_at;
"""

SELECT_SMS_ENDPOINT = """
SELECT
    user_id,
    endpoint_key,
    phone_number,
    created_at,
    updated_at
FROM sms_endpoints
WHERE user_id = ? AND endpoint_key = ?;
"""

SELECT_SMS_ENDPOINTS_BY_USER = """
SELECT
    user_id,
    endpoint_key,
    phone_number,
    created_at,
    updated_at
FROM sms_endpoints
WHERE user_id = ?
ORDER BY endpoint_key ASC;
"""

DELETE_SMS_ENDPOINT = """
DELETE FROM sms_endpoints
WHERE user_id = ? AND endpoint_key = ?;
"""

