Feature: Consume auth code
  In order to authenticate without passwords
  As a Boomerang user
  I want to consume a valid auth code

  Background:
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
            ttl_seconds: 5
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """

  @email_notifier_rpc_ready_1
  Scenario: Consume a valid auth code
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code call succeeds with HTTP 200
      """
      {}
      """
    And an "email.alerting.notification.requested" event is published
      """
      {
        "message": {
          "context": {
            "data": {
              "auth_code": "[CODE]"
            }
          }
        }
      }
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {
          "code": "[LAST_CODE]"
        }
      }
      """
    Then the consume-auth-code call succeeds with HTTP 200
      """
      {
        "access_token": "[ACCESS_TOKEN]",
        "token_type": "Bearer"
      }
      """

  Scenario: Reject consume request when token is missing
    When I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {}
      }
      """
    Then the consume-auth-code call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject consume request when token is unknown
    When I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {
          "code": "123456"
        }
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  @email_notifier_rpc_ready_1
  Scenario: Reject consume request when token is expired
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code call succeeds with HTTP 200
      """
      {}
      """
    And an "email.alerting.notification.requested" event is published
      """
      {
        "message": {
          "context": {
            "data": {
              "auth_code": "[CODE]"
            }
          }
        }
      }
      """
    When I wait 6 seconds
    And I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {
          "code": "[LAST_CODE]"
        }
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  @email_notifier_rpc_ready_1
  Scenario: Reject consume request when token is already used
    When I call POST on the identity service on http://127.0.0.1:8000/auth/request-auth-code with the following request
      """
      {
        "payload": {
          "email": "user@example.org"
        }
      }
      """
    Then the request-auth-code call succeeds with HTTP 200
      """
      {}
      """
    And an "email.alerting.notification.requested" event is published
      """
      {
        "message": {
          "context": {
            "data": {
              "auth_code": "[CODE]"
            }
          }
        }
      }
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {
          "code": "[LAST_CODE]"
        }
      }
      """
    Then the consume-auth-code call succeeds with HTTP 200
      """
      {
        "access_token": "[ACCESS_TOKEN]",
        "token_type": "Bearer"
      }
      """
    When I call POST on the identity service on http://127.0.0.1:8000/auth/consume-auth-code with the following request
      """
      {
        "payload": {
          "code": "[LAST_CODE]"
        }
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

