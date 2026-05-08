Feature: Request auth code via RPC
  In order to authenticate without passwords
  As another Boomerang service
  I want to request an auth code over RPC

  @email_notifier_rpc_ready_1
  Scenario: Request an auth code with a valid email via RPC
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

  Scenario: Reject request when email format is invalid via RPC
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
        "email": "not-an-email"
      }
      """
    Then the request_auth_code request is rejected due to validation error
      """
      {
        "code": "INTERNAL_ERROR",
        "message": "Invalid request payload."
      }
      """
