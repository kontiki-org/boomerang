@sms_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing SMS from the alerting pipeline
  As the sms-notifier service
  I want to consume "alerting.notification.requested" events for the SMS channel

  Background:
    Given the sms-notifier service is running with the following configuration
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
            filename: /tmp/sms-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/sms_notifier/tests/integration/db/sms_notifier.sqlite3
        sms:
          provider:
            base_url: http://127.0.0.1:18080
            api_key: test-key
            sender_id: BOOMERANG
      """

  Scenario: Consume a valid SMS notification request
    When an "alerting.notification.requested" event is published with payload
      """
      {
        "channel": "sms",
        "destination": {
          "kind": "phone_number",
          "value": "+33612345678"
        },
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
    Then the sms provider should contain a message matching
      """
      {
        "to": "+33612345678",
        "body_contains": [
          "Storm warning for your area."
        ]
      }
      """
    And a "alerting.notification.delivered" event is published
      """
      {
        "status": "delivered",
        "channel": "sms"
      }
      """

  Scenario: Ignore a notification request for a non-sms channel
    When an "alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "destination": {
          "kind": "email_address",
          "value": "user@example.org"
        },
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
    Then the sms-notifier service ignores the event

  Scenario: Reject malformed notification payload
    Given the sms provider will respond with HTTP 400
      """
      {
        "status": "error",
        "message": "invalid destination"
      }
      """
    When an "alerting.notification.requested" event is published with payload
      """
      {
        "channel": "sms",
        "destination": {
          "kind": "phone_number",
          "value": ""
        },
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
    Then the sms-notifier service rejects the event as invalid payload
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
