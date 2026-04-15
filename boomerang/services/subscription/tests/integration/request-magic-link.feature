Feature: Request magic link
  In order to authenticate without passwords
  As a Boomerang subscription user
  I want to request a magic link with my email

  Scenario: Request a magic link with a valid email
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
            ttl_seconds: 30
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
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

  Scenario: Reject request when email is missing
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
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {}
      """
    Then the request-magic-link call is rejected with HTTP 400
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject request when email format is invalid
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
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "not-an-email"
      }
      """
    Then the request-magic-link call is rejected with HTTP 400
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject request when rate limit is exceeded
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
            ttl_seconds: 30
            cooldown_seconds: 1
            rate_limit:
              max_requests: 3
              window_seconds: 8
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 2 seconds
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 2 seconds
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 2 seconds
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-magic-link call is rejected with HTTP 429
      """
      {
        "message": "Too many requests. Please try again later."
      }
      """

  Scenario: Reject request during cooldown window for same email
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
            ttl_seconds: 30
            cooldown_seconds: 2
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 1 second
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    Then the request-magic-link call is rejected with HTTP 429
      """
      {
        "message": "Too many requests. Please try again later."
      }
      """

  Scenario: Accept request once cooldown window has expired
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
            ttl_seconds: 30
            cooldown_seconds: 1
            rate_limit:
              max_requests: 5
              window_seconds: 8
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 2 seconds
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
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

  Scenario: Accept request once rate limit window has expired
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
            ttl_seconds: 30
            cooldown_seconds: 0
            rate_limit:
              max_requests: 2
              window_seconds: 2
      """
    When I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
      """
      {
        "email": "user@example.org"
      }
      """
    And I wait 3 seconds
    And I call request-magic-link on the subscription service on http://127.0.0.1:8000 with the following payload
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
