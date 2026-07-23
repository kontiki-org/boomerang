@configured_endpoints_rpc
Feature: Configured endpoints loaded from telegram-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want Telegram endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen) — independent of audience.
  Dispatch resolves endpoint_key against this registry; recipient_id (audience from subscriptions) is opaque to the notifier.

  Scenario: Deliver notification using configured endpoint
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
        "text": "🟠 <b>Registry</b>\n\nRegistry alert\n\n<b>Message:</b> payment-service degraded.",
        "parse_mode": "HTML"
      }
      """
    And a "alerting.notification.delivered" event is published
      """
      {
        "status": "delivered",
        "channel": "telegram"
      }
      """

  Scenario: Deliver to multiple configured endpoints
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
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "111222333"
          telegram_primary:
            chat_id: "987654321"
      """
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
        "text": "🟢 <b>Registry</b>\n\nOps alert\n\n<b>Message:</b> Configured endpoint delivery.",
        "parse_mode": "HTML"
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
          "body": "Second configured endpoint delivery.",
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
        "text": "🟡 <b>Earthquake</b>\n\nUI alert\n\n<b>Message:</b> Second configured endpoint delivery.",
        "parse_mode": "HTML"
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
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: ""
      """
    Then the telegram-notifier service startup error mentions endpoints
