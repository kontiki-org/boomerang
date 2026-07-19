@configured_endpoints_rpc
Feature: Configured endpoints loaded from email-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want email endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen) — independent of owner.
  Dispatch resolves endpoint_key against this registry; recipient_id (owner) comes from subscriptions.
  SQLite endpoints remain for seeded / legacy rows; YAML is the primary OSS path.

  Scenario: Deliver notification using configured endpoint when SQLite is empty
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
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/email_notifier/tests/integration/db/email_notifier.sqlite3
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
        "subject": "Registry alert",
        "body_contains": [
          "payment-service degraded."
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

  Scenario: Coexist configured and SQLite endpoints for different owners
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
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/email_notifier/tests/integration/db/email_notifier.sqlite3
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
    And the "email_endpoints" table contains
      | user_id | endpoint_key  | address          |
      | usr_ui  | email_primary | user@example.org |
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
        "subject": "Ops alert",
        "body_contains": [
          "Configured endpoint delivery."
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
          "body": "SQLite endpoint delivery.",
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
        "subject": "UI alert",
        "body_contains": [
          "SQLite endpoint delivery."
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
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/email_notifier/tests/integration/db/email_notifier.sqlite3
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
