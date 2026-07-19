@email_notifier_degradation
Feature: Report degraded state for email-notifier service
  In order to make service health visible in the service registry
  As an operator of the alerting platform
  I want email-notifier to expose a degraded state when SMTP delivery is unhealthy

  Background:
    Given the email-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        heartbeat:
          interval: 1
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
            port: 1
            use_starttls: false
            username: ""
            password: ""
          from:
            address: no-reply@example.org
        endpoints:
          email_primary:
            address: user@example.org
      """

  Scenario: Service becomes degraded after repeated SMTP failures
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
            "data": {}
          }
        }
      }
      """
    And an "email.alerting.notification.requested" event is published with payload
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
    And an "email.alerting.notification.requested" event is published with payload
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
    Then the service registry eventually receives a heartbeat with degraded flag true
