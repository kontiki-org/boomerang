Feature: Verify session via RPC
  In order to authorize authenticated users
  As another Boomerang service
  I want to verify an access token over RPC

  @email_notifier_rpc_ready_1
  Scenario: Verify a valid access token via RPC
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
    When I call the RPC request_auth_code on the identity service with the following arguments
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request_auth_code RPC call succeeds
    And an "email.alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "recipient_id": "[USER_ID]",
        "endpoint_key": "email_primary",
        "message": {
          "title": "Boomerang sign in",
          "body": "Use this verification code to sign in: [CODE].",
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
    When I call the RPC consume_auth_code on the identity service with the following arguments
      """
      {
        "code": "[LAST_CODE]"
      }
      """
    Then the consume_auth_code RPC call succeeds
    And the consume_auth_code RPC response is
      """
      {
        "access_token": "[ACCESS_TOKEN]",
        "token_type": "Bearer"
      }
      """
    When I call the RPC verify_session on the identity service with the following arguments
      """
      {
        "access_token": "[LAST_ACCESS_TOKEN]"
      }
      """
    Then the verify_session RPC call succeeds
    And the verify_session RPC response is
      """
      {
        "user_id": "[USER_ID]",
        "email": "user@example.org",
        "session_expires_at": "[ISO8601_UTC]",
        "cache_valid_until": "[ISO8601_UTC]"
      }
      """

  Scenario: Reject verify session when access token does not exist via RPC
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
    When I call the RPC verify_session on the identity service with the following arguments
      """
      {
        "access_token": "invalid-token"
      }
      """
    Then the verify_session request is rejected due to auth error
      """
      {
        "code": "AUTH_ERROR",
        "message": "Authentication required or invalid."
      }
      """
