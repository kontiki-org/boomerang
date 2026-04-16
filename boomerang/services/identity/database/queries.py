CREATE_AUTH_CODES_TABLE = """
CREATE TABLE IF NOT EXISTS auth_codes (
  code TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  used INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
"""

CREATE_AUTH_CODES_EMAIL_INDEX = """
CREATE INDEX IF NOT EXISTS idx_auth_codes_email
ON auth_codes (email);
"""

CREATE_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS sessions (
  access_token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  email TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

CREATE_SESSIONS_USER_INDEX = """
CREATE INDEX IF NOT EXISTS idx_sessions_user
ON sessions (user_id);
"""

INSERT_AUTH_CODE = """
INSERT INTO auth_codes (code, email, expires_at, used, created_at)
VALUES (?, ?, ?, ?, ?);
"""

SELECT_AUTH_CODE = """
SELECT code, email, expires_at, used
FROM auth_codes
WHERE code = ?;
"""

MARK_AUTH_CODE_USED = """
UPDATE auth_codes
SET used = 1
WHERE code = ?;
"""

INSERT_SESSION = """
INSERT INTO sessions (access_token, user_id, email, expires_at, created_at)
VALUES (?, ?, ?, ?, ?);
"""

SELECT_SESSION = """
SELECT access_token, user_id, email, expires_at
FROM sessions
WHERE access_token = ?;
"""

DELETE_EXPIRED_AUTH_CODES = """
DELETE FROM auth_codes
WHERE expires_at < ?;
"""

DELETE_EXPIRED_SESSIONS = """
DELETE FROM sessions
WHERE expires_at < ?;
"""
