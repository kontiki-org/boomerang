@email_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing emails from the alerting pipeline
  As the email-notifier service
  I want to consume "email.alerting.notification.requested" events for the email channel

  Background:
    Given the email-notifier service is running with the following configuration
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
            filename: /tmp/email-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        email:
          smtp:
            host: 127.0.0.1
            port: 1025
            use_starttls: false
            username: ""
            password: ""
          from:
            address: no-reply@example.org
        endpoints:
          email_primary:
            address: user@example.org
      """

  Scenario: Consume a valid email notification request
    When an "email.alerting.notification.requested" event is published with payload
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
            "data": {
              "category": "weather.wind",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then MailHog should contain an email matching
      """
      {
        "from": "no-reply@example.org",
        "to": ["user@example.org"],
        "subject": "Weather alert",
        "body_contains": [
          "Storm warning for your area."
        ]
      }
      """
    And a "alerting.notification.delivered" event is published
      """
      {
        "status": "delivered",
        "channel": "email"
      }
      """

  Scenario: Ignore a notification request for a non-email channel
    When an "email.alerting.notification.requested" event is published with payload
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
            "data": {}
          }
        }
      }
      """
    Then the email-notifier service ignores the event

  Scenario: Reject malformed notification payload
    When an "email.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
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
    Then the email-notifier service rejects the event as invalid payload
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
