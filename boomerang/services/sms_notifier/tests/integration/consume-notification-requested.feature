@sms_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing SMS from the alerting pipeline
  As the sms-notifier service
  I want to consume "sms.alerting.notification.requested" events for the SMS channel

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
    Given the "sms_endpoints" table contains
      | user_id | endpoint_key | phone_number |
      | usr_1   | sms_primary  | +33612345678 |
    When an "sms.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "sms",
        "recipient_id": "usr_1",
        "endpoint_key": "sms_primary",
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
    When an "sms.alerting.notification.requested" event is published with payload
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
    Then the sms-notifier service ignores the event

  Scenario: Reject malformed notification payload
    Given the sms provider will respond with HTTP 400
      """
      {
        "status": "error",
        "message": "invalid destination"
      }
      """
    When an "sms.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "sms",
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
