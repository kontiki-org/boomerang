@configured_endpoints_rpc
Feature: Configured endpoints loaded from telegram-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want Telegram endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen) — independent of owner.
  Dispatch resolves endpoint_key against this registry; recipient_id (owner) comes from subscriptions. SQLite endpoints keep user_id from identity (platform profile).

  Scenario: Deliver notification using configured endpoint when SQLite is empty
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/telegram_notifier/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "123456789"
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "platform-ops",
        "endpoint_key": "ops_alerts",
        "message": {
          "title": "Registry alert",
          "body": "payment-service degraded.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "state_changed",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text_contains": [
          "Registry alert",
          "payment-service degraded."
        ]
      }
      """
    And a "alerting.notification.delivered" event is published
      """
      {
        "status": "delivered",
        "channel": "telegram"
      }
      """

  Scenario: Coexist configured and SQLite endpoints for different owners
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/telegram_notifier/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "111222333"
      """
    And the "telegram_endpoints" table contains
      | user_id | endpoint_key     | chat_id   |
      | usr_ui  | telegram_primary | 987654321 |
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "platform-ops",
        "endpoint_key": "ops_alerts",
        "message": {
          "title": "Ops alert",
          "body": "Configured endpoint delivery.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "state_changed",
              "severity": "low"
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "111222333",
        "text_contains": [
          "Ops alert",
          "Configured endpoint delivery."
        ]
      }
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_ui",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "UI alert",
          "body": "SQLite endpoint delivery.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "natural.earthquake",
              "event_type": "earthquake",
              "severity": "moderate"
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "987654321",
        "text_contains": [
          "UI alert",
          "SQLite endpoint delivery."
        ]
      }
      """

  @identity_sessions_1
  Scenario: Configured endpoints are not returned by list_endpoints
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/telegram_notifier/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "123456789"
      """
    And I am authenticated as "user@example.org"
    When I call the RPC list_endpoints on the telegram-notifier service with the following arguments
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {
        "endpoints": []
      }
      """

  Scenario: Reject invalid configured endpoint at service startup
    When the telegram-notifier service fails to start with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/telegram_notifier/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: ""
      """
    Then the telegram-notifier service startup error mentions endpoints
