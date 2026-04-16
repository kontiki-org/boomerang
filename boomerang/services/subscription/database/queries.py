"""
Subscription service schema.

Identity data (email, sessions, auth codes) is owned by identity-service.
This DB stores only subscription records keyed by the opaque user_id.
"""

CREATE_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    alert TEXT NOT NULL,
    event_type TEXT NOT NULL,
    area_type TEXT NOT NULL,
    area_value TEXT NOT NULL,
    min_severity TEXT NOT NULL DEFAULT 'moderate',
    delivery_json TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_SUBSCRIPTIONS_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_subscriptions_user
ON subscriptions(user_id);
"""

CREATE_SUBSCRIPTIONS_LOOKUP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_subscriptions_lookup
ON subscriptions(alert, area_type, area_value, status);
"""

CREATE_SUBSCRIPTIONS_IDENTITY_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_subscriptions_identity
ON subscriptions(user_id, alert, event_type, area_type, area_value, min_severity);
"""

INSERT_OR_IGNORE_SUBSCRIPTION = """
INSERT OR IGNORE INTO subscriptions (
    subscription_id,
    user_id,
    alert,
    event_type,
    area_type,
    area_value,
    min_severity,
    delivery_json,
    policy_json,
    status,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?);
"""

SELECT_SUBSCRIPTIONS_BY_USER = """
SELECT
    subscription_id,
    user_id,
    alert,
    event_type,
    area_type,
    area_value,
    min_severity,
    delivery_json,
    policy_json,
    status,
    created_at,
    updated_at
FROM subscriptions
WHERE user_id = ?
ORDER BY created_at DESC;
"""

SELECT_SUBSCRIPTION_BY_ID_AND_USER = """
SELECT
    subscription_id,
    user_id,
    alert,
    event_type,
    area_type,
    area_value,
    min_severity,
    delivery_json,
    policy_json,
    status,
    created_at,
    updated_at
FROM subscriptions
WHERE subscription_id = ? AND user_id = ?
LIMIT 1;
"""

UPDATE_SUBSCRIPTION = """
UPDATE subscriptions
SET
    min_severity = ?,
    policy_json = ?,
    status = ?,
    updated_at = ?
WHERE subscription_id = ? AND user_id = ?;
"""

DELETE_SUBSCRIPTION = """
DELETE FROM subscriptions
WHERE subscription_id = ? AND user_id = ?;
"""

CREATE_CHANNEL_ENDPOINTS_TABLE = """
CREATE TABLE IF NOT EXISTS channel_endpoints (
    endpoint_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    endpoint_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_CHANNEL_ENDPOINTS_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_channel_endpoints_user
ON channel_endpoints(user_id);
"""

CREATE_CHANNEL_ENDPOINTS_UNIQUE_KEY = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_channel_endpoints_user_channel_key
ON channel_endpoints(user_id, channel, endpoint_key);
"""

INSERT_OR_IGNORE_CHANNEL_ENDPOINT = """
INSERT OR IGNORE INTO channel_endpoints (
    endpoint_id,
    user_id,
    channel,
    endpoint_key,
    status,
    is_default,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, 'active', ?, ?, ?);
"""

SELECT_CHANNEL_ENDPOINT_BY_KEY = """
SELECT
    endpoint_id,
    user_id,
    channel,
    endpoint_key,
    status,
    is_default,
    created_at,
    updated_at
FROM channel_endpoints
WHERE user_id = ? AND channel = ? AND endpoint_key = ?
LIMIT 1;
"""
