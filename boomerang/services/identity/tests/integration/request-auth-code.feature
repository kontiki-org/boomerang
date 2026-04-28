Feature: Request auth code
  In order to authenticate without passwords
  As a Boomerang user
  I want to request an auth code with my email

  @email_notifier_rpc_ready_1
  Scenario: Request an auth code with a valid email
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """
    And the identity service calls email-notifier RPC ensure_auth_email_endpoint with
      """
      ["[USER_ID]", "email_primary", "user@example.org"]
      """
    And an "email.alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "recipient_id": "[USER_ID]",
        "endpoint_key": "email_primary",
        "message": {
          "title": "Boomerang sign in",
          "body": "Use this verification code to sign in.",
          "context": {
            "kind": "auth.code",
            "data": {
              "auth_code": "[CODE]",
              "expires_at": "[ISO8601_UTC]"
            }
          }
        }
      }
      """

  Scenario: Reject request when email is missing
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {}
      }
      """
    Then the request-auth-code call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject request when email format is invalid
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "not-an-email"
        }
      }
      """
    Then the request-auth-code call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """

  @email_notifier_rpc_ready_4
  Scenario: Reject request when rate limit is exceeded
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 1
            rate_limit:
              max_requests: 3
              window_seconds: 8
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 2 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 2 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 2 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code call is rejected with HTTP 429
      """
      {
        "message": "Too many requests. Please try again later."
      }
      """

  @email_notifier_rpc_ready_2
  Scenario: Reject request during cooldown window for same email
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 1 second
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code call is rejected with HTTP 429
      """
      {
        "message": "Too many requests. Please try again later."
      }
      """

  @email_notifier_rpc_ready_2
  Scenario: Accept request once cooldown window has expired
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 1
            rate_limit:
              max_requests: 5
              window_seconds: 8
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 2 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """

  @email_notifier_rpc_ready_3
  Scenario: Accept request once rate limit window has expired
    Given the identity service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8000
      logging:
        version: 1
        disable_existing_loggers: false
        formatters:
          default:
            format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            datefmt: "%Y-%m-%d %H:%M:%S"
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/identity.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/identity/tests/integration/db/identity.sqlite3
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 0
            rate_limit:
              max_requests: 2
              window_seconds: 2
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    And I wait 3 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """

