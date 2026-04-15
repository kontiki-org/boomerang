Feature: Consume magic link
  In order to authenticate without passwords
  As a Boomerang subscription user
  I want to consume a valid magic link token

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
          magic_link:
            ttl_seconds: 5
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """

  Scenario: Consume a valid magic link token
    When I call the subscription service on http://127.0.0.1:8000/auth/request-magic-link with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-magic-link response is
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
          "body": "Use this link to sign in.",
          "context": {
            "kind": "auth.magic_link",
            "data": {
              "magic_link_url": "http://localhost:8000/auth/consume-magic-link?token=[TOKEN]",
              "expires_at": "[ISO8601_UTC]"
            }
          }
        }
      }
      """
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {
        "token": "[LAST_TOKEN]"
      }
      """
    Then the consume-magic-link response is
      """
      {
        "status": "ok"
      }
      """

  Scenario: Reject consume request when token is missing
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {}
      """
    Then the consume-magic-link call is rejected with HTTP 400
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject consume request when token is unknown
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {
        "token": "unknown-token"
      }
      """
    Then the consume-magic-link call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject consume request when token is expired
    When I call the subscription service on http://127.0.0.1:8000/auth/request-magic-link with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-magic-link response is
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
          "body": "Use this link to sign in.",
          "context": {
            "kind": "auth.magic_link",
            "data": {
              "magic_link_url": "http://localhost:8000/auth/consume-magic-link?token=[TOKEN]",
              "expires_at": "[ISO8601_UTC]"
            }
          }
        }
      }
      """
    When I wait 6 seconds
    And I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {
        "token": "[LAST_TOKEN]"
      }
      """
    Then the consume-magic-link call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject consume request when token is already used
    When I call the subscription service on http://127.0.0.1:8000/auth/request-magic-link with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-magic-link response is
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
          "body": "Use this link to sign in.",
          "context": {
            "kind": "auth.magic_link",
            "data": {
              "magic_link_url": "http://localhost:8000/auth/consume-magic-link?token=[TOKEN]",
              "expires_at": "[ISO8601_UTC]"
            }
          }
        }
      }
      """
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {
        "token": "[LAST_TOKEN]"
      }
      """
    Then the consume-magic-link response is
      """
      {
        "status": "ok"
      }
      """
    When I call the subscription service on http://127.0.0.1:8000/auth/consume-magic-link with the following payload
      """
      {
        "token": "[LAST_TOKEN]"
      }
      """
    Then the consume-magic-link call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """
