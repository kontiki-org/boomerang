@telegram_notifier_degradation
Feature: Report degraded state for telegram-notifier service
  In order to make service health visible in the service registry
  As an operator of the alerting platform
  I want telegram-notifier to expose a degraded state when Telegram API delivery is unhealthy

  Background:
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        heartbeat:
          interval: 1
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
          api_base_url: http://127.0.0.1:1
        endpoints:
          telegram_primary:
            chat_id: "123456789"
      """

  Scenario: Service becomes degraded after repeated Telegram API failures
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    And an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    And an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    Then the service registry eventually receives a heartbeat with degraded flag true
