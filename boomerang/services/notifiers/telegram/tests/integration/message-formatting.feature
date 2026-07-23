@telegram_notifier_events
Feature: Telegram structured message formatting
  In order to render alerts without hardcoding domain tables
  As the telegram-notifier service
  I want category icons from configuration and automatic attribute labels

  Scenario: Apply a category icon from configuration (exact match)
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
          category_icons:
            natural.earthquake: "🌍"
            weather: "🌧"
        endpoints:
          telegram_primary:
            chat_id: "123456789"
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "M 2.3 - Honey Lake",
          "body": "M 2.3 - Honey Lake",
          "context": {
            "kind": "alert",
            "data": {
              "category": "natural.earthquake",
              "severity": "low",
              "attributes": {
                "magnitude": 2.3
              }
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🌍 🟢 <b>Earthquake</b>\n\n<b>Magnitude:</b> 2.3",
        "parse_mode": "HTML"
      }
      """

  Scenario: Apply a category icon from configuration (prefix match)
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
          category_icons:
            weather: "🌧"
        endpoints:
          telegram_primary:
            chat_id: "123456789"
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Wind alert",
          "body": "Strong winds expected.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "weather.wind",
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
        "text": "🌧 🟠 <b>Wind</b>\n\nWind alert\n\n<b>Message:</b> Strong winds expected.",
        "parse_mode": "HTML"
      }
      """

  Scenario: Humanize attribute keys and keep producer insertion order
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
          telegram_primary:
            chat_id: "123456789"
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Website down",
          "body": "Website down",
          "context": {
            "kind": "alert",
            "data": {
              "category": "website.http",
              "severity": "critical",
              "attributes": {
                "response_time": "2.4s",
                "status_code": 503,
                "service": "checkout"
              }
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🔴 <b>Http</b>\n\n<b>Response Time:</b> 2.4s\n<b>Status Code:</b> 503\n<b>Service:</b> checkout",
        "parse_mode": "HTML"
      }
      """

  Scenario: Show Message body when it differs from the title even with attributes
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
          telegram_primary:
            chat_id: "123456789"
      """
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Certificate expiry",
          "body": "SSL handshake failed: certificate has expired",
          "context": {
            "kind": "alert",
            "data": {
              "category": "certificate",
              "severity": "severe",
              "attributes": {
                "service": "api.example.com"
              }
            }
          }
        }
      }
      """
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🟠 <b>Certificate</b>\n\n<b>Service:</b> api.example.com\n\n<b>Message:</b> SSL handshake failed: certificate has expired",
        "parse_mode": "HTML"
      }
      """
