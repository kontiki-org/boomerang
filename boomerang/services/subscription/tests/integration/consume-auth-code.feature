Feature: Consume auth code
  In order to authenticate without passwords
  As a Boomerang subscription user
  I want to consume a valid auth code

  Background:
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        auth:
          auth_code:
            ttl_seconds: 5
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """

  Scenario: Consume a valid auth code
    When I call the subscription service on http://127.0.0.1:8000/auth/request-auth-code with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """
    And a "alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "destination": {
          "kind": "email_address",
          "value": "user@example.org"
        },
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
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {
        "code": "[LAST_CODE]"
      }
      """
    Then the consume-auth-code response is
      """
      {
        "status": "ok",
        "access_token": "[ACCESS_TOKEN]",
        "token_type": "Bearer"
      }
      """

  Scenario: Reject consume request when token is missing
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {}
      """
    Then the consume-auth-code call is rejected with HTTP 400
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject consume request when token is unknown
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {
        "code": "123456"
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject consume request when token is expired
    When I call the subscription service on http://127.0.0.1:8000/auth/request-auth-code with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """
    And a "alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "destination": {
          "kind": "email_address",
          "value": "user@example.org"
        },
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
    When I wait 6 seconds
    And I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {
        "code": "[LAST_CODE]"
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject consume request when token is already used
    When I call the subscription service on http://127.0.0.1:8000/auth/request-auth-code with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-auth-code response is
      """
      {
        "status": "ok"
      }
      """
    And a "alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "destination": {
          "kind": "email_address",
          "value": "user@example.org"
        },
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
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {
        "code": "[LAST_CODE]"
      }
      """
    Then the consume-auth-code response is
      """
      {
        "status": "ok",
        "access_token": "[ACCESS_TOKEN]",
        "token_type": "Bearer"
      }
      """
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-auth-code with the following payload
      """
      {
        "code": "[LAST_CODE]"
      }
      """
    Then the consume-auth-code call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """
