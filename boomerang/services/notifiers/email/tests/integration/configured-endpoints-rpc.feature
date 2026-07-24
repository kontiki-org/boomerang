@configured_endpoints_rpc
Feature: Configured endpoints loaded from email-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want email endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen) — independent of audience.
  Dispatch resolves endpoint_key against this registry; recipient_id (audience from subscriptions) is opaque to the notifier.

  Scenario: Deliver notification using configured endpoint
    Given the email-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8003
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
          oncall:
            address: ops@example.org
      """
    When an "email.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "recipient_id": "platform-ops",
        "endpoint_key": "oncall",
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
    Then MailHog should contain an email matching
      """
      {
        "from": "no-reply@example.org",
        "to": ["ops@example.org"],
        "subject": "State Changed",
        "body_contains": [
          "State Changed",
          "Registry alert",
          "Message: payment-service degraded.",
          "<b>State Changed</b>"
        ]
      }
      """

  Scenario: Deliver to multiple configured endpoints
    Given the email-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8003
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
          oncall:
            address: ops@example.org
          email_primary:
            address: user@example.org
      """
    When an "email.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "recipient_id": "platform-ops",
        "endpoint_key": "oncall",
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
    Then MailHog should contain an email matching
      """
      {
        "from": "no-reply@example.org",
        "to": ["ops@example.org"],
        "subject": "State Changed",
        "body_contains": [
          "State Changed",
          "Ops alert",
          "Message: Configured endpoint delivery.",
          "<b>State Changed</b>"
        ]
      }
      """
    When an "email.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "email",
        "recipient_id": "usr_ui",
        "endpoint_key": "email_primary",
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
    Then MailHog should contain an email matching
      """
      {
        "from": "no-reply@example.org",
        "to": ["user@example.org"],
        "subject": "Earthquake",
        "body_contains": [
          "Earthquake",
          "UI alert",
          "Message: Second configured endpoint delivery.",
          "<b>Earthquake</b>"
        ]
      }
      """

  Scenario: Reject invalid configured endpoint at service startup
    When the email-notifier service fails to start with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8003
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
          oncall:
            address: ""
      """
    Then the email-notifier service startup error mentions endpoints
