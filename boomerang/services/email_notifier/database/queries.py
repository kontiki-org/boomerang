"""
Email notifier service schema.

This DB stores only email endpoints keyed by the opaque user_id and endpoint_key.
"""

CREATE_EMAIL_ENDPOINTS_TABLE = """
CREATE TABLE IF NOT EXISTS email_endpoints (
    user_id TEXT NOT NULL,
    endpoint_key TEXT NOT NULL,
    address TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, endpoint_key)
);
"""

UPSERT_EMAIL_ENDPOINT = """
INSERT INTO email_endpoints (
    user_id,
    endpoint_key,
    address,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?)
ON CONFLICT(user_id, endpoint_key) DO UPDATE SET
    address = excluded.address,
    updated_at = excluded.updated_at;
"""

SELECT_EMAIL_ENDPOINT = """
SELECT
    user_id,
    endpoint_key,
    address,
    created_at,
    updated_at
FROM email_endpoints
WHERE user_id = ? AND endpoint_key = ?;
"""

