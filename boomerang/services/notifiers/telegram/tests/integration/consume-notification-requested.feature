@telegram_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing Telegram messages from the alerting pipeline
  As the telegram-notifier service
  I want to consume "telegram.alerting.notification.requested" events for the telegram channel

  Background:
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

  Scenario: Consume a valid telegram notification request
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
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
        "text": "🟠 <b>Wind</b>\n\nWeather alert\n\n<b>Message:</b> Storm warning for your area.",
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

  Scenario: Format a structured earthquake alert without category icons
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "telegram_primary",
        "message": {
          "title": "M 2.3 - 24 km ENE of Honey Lake, CA",
          "body": "M 2.3 - 24 km ENE of Honey Lake, CA. Detail: https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766",
          "context": {
            "kind": "alert",
            "data": {
              "alert_id": "usgs_nc75395766",
              "category": "natural.earthquake",
              "event_type": "earthquake",
              "severity": "low",
              "attributes": {
                "magnitude": 2.3,
                "place": "24 km ENE of Honey Lake, CA",
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766"
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
        "text": "🟢 <b>Earthquake</b>\n\n<b>Magnitude:</b> 2.3\n<b>Place:</b> 24 km ENE of Honey Lake, CA\n\n🔗 <a href=\"https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766\">Details</a>",
        "parse_mode": "HTML"
      }
      """

  Scenario: Ignore a notification request for a non-telegram channel
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "recipient_id": "usr_1",
        "endpoint_key": "email_primary",
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
    Then the telegram-notifier service ignores the event

  Scenario: Reject malformed notification payload
    When an "telegram.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "telegram",
        "recipient_id": "usr_1",
        "endpoint_key": "",
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
    Then the telegram-notifier service rejects the event as invalid payload
    And a "alerting.notification.failed" event is published
      """
      {
        "status": "failed",
        "error": {
          "type": "delivery_error",
          "message": "[ERROR]"
        }
      }
      """
