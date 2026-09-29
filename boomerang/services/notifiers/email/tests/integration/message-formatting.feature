@email_notifier_events
Feature: Email structured message formatting
  In order to render alerts like Telegram without hardcoding domain tables
  As the email-notifier service
  I want multipart plain+HTML emails with event_type banner and attribute rows

  Scenario: Structured alert uses event_type subject and attribute rows
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
    When an "email.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "endpoint_key": "email_primary",
        "message": {
          "title": "demo-app-service state active → degraded",
          "body": "demo-app-service state active → degraded",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "instance_state_changed",
              "severity": "severe",
              "attributes": {
                "service_name": "demo-app-service",
                "previous_state": "active",
                "new_state": "degraded",
                "reason": "demo degrade requested"
              }
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
        "subject": "Instance State Changed",
        "body_contains": [
          "Instance State Changed",
          "Service Name: demo-app-service",
          "Previous State: active",
          "New State: degraded",
          "Reason: demo degrade requested",
          "<b>Service Name:</b>",
          "<b>Reason:</b> demo degrade requested"
        ]
      }
      """
