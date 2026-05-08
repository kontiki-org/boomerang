Feature: Consume auth code via RPC
  In order to authenticate without passwords
  As another Boomerang service
  I want to consume an auth code over RPC

  @email_notifier_rpc_ready_1
  Scenario: Consume a valid auth code via RPC
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
    And the request_auth_code RPC response is
      """
      {}
      """
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

  Scenario: Reject consume when auth code does not exist via RPC
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
    When I call the RPC consume_auth_code on the identity service with the following arguments
      """
      {
        "code": "123456"
      }
      """
    Then the consume_auth_code request is rejected due to auth error
      """
      {
        "code": "AUTH_ERROR",
        "message": "Authentication required or invalid."
      }
      """
