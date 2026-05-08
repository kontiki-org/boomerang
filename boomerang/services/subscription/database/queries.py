"""
Subscription service schema.

Identity data (email, sessions, auth codes) is owned by identity-service.
This DB stores only subscription records keyed by the opaque user_id.
"""

CREATE_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    event_type TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    endpoints_json TEXT NOT NULL,
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
ON subscriptions(category, event_type, status);
"""

CREATE_SUBSCRIPTIONS_IDENTITY_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_subscriptions_identity
ON subscriptions(user_id, category, event_type, criteria_json, endpoints_json);
"""

INSERT_OR_IGNORE_SUBSCRIPTION = """
INSERT OR IGNORE INTO subscriptions (
    subscription_id,
    user_id,
    category,
    event_type,
    criteria_json,
    endpoints_json,
    status,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?);
"""

SELECT_SUBSCRIPTIONS_BY_USER = """
SELECT
    subscription_id,
    user_id,
    category,
    event_type,
    criteria_json,
    endpoints_json,
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
    category,
    event_type,
    criteria_json,
    endpoints_json,
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
    category = ?,
    event_type = ?,
    criteria_json = ?,
    endpoints_json = ?,
    status = ?,
    updated_at = ?
WHERE subscription_id = ? AND user_id = ?;
"""

DELETE_SUBSCRIPTION = """
DELETE FROM subscriptions
WHERE subscription_id = ? AND user_id = ?;
"""

SELECT_RECIPIENT_CANDIDATES_FOR_ALERT = """
SELECT
    s.user_id,
    s.criteria_json,
    s.endpoints_json
FROM subscriptions AS s
WHERE s.status = 'active'
  AND s.category = ?
  AND (s.event_type = ? OR s.event_type = '*')
;
"""
