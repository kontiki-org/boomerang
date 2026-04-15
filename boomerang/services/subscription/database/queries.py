CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

CREATE_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    category TEXT NOT NULL,
    event_type TEXT NOT NULL,
    area_type TEXT NOT NULL,
    area_value TEXT NOT NULL,
    min_severity TEXT NOT NULL DEFAULT 'moderate',
    delivery_json TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
"""

CREATE_USERS_EMAIL_INDEX = "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
CREATE_SUBSCRIPTIONS_USER_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)"
)

CREATE_SUBSCRIPTIONS_LOOKUP_INDEX = """
CREATE INDEX IF NOT EXISTS idx_subscriptions_lookup
ON subscriptions(category, area_type, area_value, status)
"""

CREATE_SUBSCRIPTIONS_IDENTITY_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_subscriptions_identity
ON subscriptions(user_id, category, event_type, area_type, area_value, min_severity)
"""

INSERT_OR_IGNORE_USER = """
INSERT OR IGNORE INTO users (
    user_id, email, display_name, status, created_at, updated_at
) VALUES (?, ?, ?, 'active', ?, ?)
"""

INSERT_OR_IGNORE_SUBSCRIPTION = """
INSERT OR IGNORE INTO subscriptions (
    subscription_id,
    user_id,
    category,
    event_type,
    area_type,
    area_value,
    min_severity,
    delivery_json,
    policy_json,
    status,
    created_at,
    updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
"""

SELECT_SUBSCRIPTIONS_BY_USER = """
SELECT
    subscription_id,
    user_id,
    category,
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
ORDER BY created_at DESC
"""

SELECT_SUBSCRIPTION_BY_ID_AND_USER = """
SELECT
    subscription_id,
    user_id,
    category,
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
LIMIT 1
"""

UPDATE_SUBSCRIPTION = """
UPDATE subscriptions
SET
    min_severity = ?,
    policy_json = ?,
    status = ?,
    updated_at = ?
WHERE subscription_id = ? AND user_id = ?
"""

DELETE_SUBSCRIPTION = """
DELETE FROM subscriptions
WHERE subscription_id = ? AND user_id = ?
"""
