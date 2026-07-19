@subscriptions_rpc
Feature: Configured subscriptions loaded from service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want subscriptions declared in service configuration to resolve recipients

  Configured entries are keyed by owner_id, then rule name (opaque, operator-chosen).
  recipient_id in dispatch equals owner_id — not the rule name.
  Configured endpoints use qualified refs "<channel>.<endpoint_id>" (e.g. telegram.ops_alerts); the loader resolves them to channel + endpoint_key at dispatch.

  Scenario: Match recipients from configured subscriptions
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        subscriptions:
          platform-ops:
            payment-degraded:
              status: active
              subscription:
                rule:
                  category: kontiki.registry
                  event_type: instance_state_changed
                  criteria:
                    all_of:
                      - key: service_name
                        operator: eq
                        value: payment-service
                endpoints:
                  - telegram.ops_alerts
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "reg_payment_degraded",
          "source": "kontiki-registry-alert-service",
          "category": "kontiki.registry",
          "event_type": "instance_state_changed",
          "severity": "severe",
          "occurred_at": "2026-07-15T12:00:00Z",
          "title": "payment-service degraded",
          "body": "Instance state changed to degraded.",
          "areas": [],
          "attributes": {
            "service_name": "payment-service",
            "previous_state": "healthy",
            "new_state": "degraded"
          }
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "recipient_id": "platform-ops",
          "channel": "telegram",
          "endpoint_key": "ops_alerts"
        }
      ]
      """

  Scenario: Match recipients from multiple configured owners for the same alert
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        subscriptions:
          platform-ops:
            earthquake-alerts:
              status: active
              subscription:
                rule:
                  category: natural.earthquake
                  event_type: earthquake
                  criteria:
                    all_of:
                      - key: magnitude
                        operator: gte
                        value: 4
                endpoints:
                  - telegram.ops_alerts
          usr_ui:
            earthquake-email:
              status: active
              subscription:
                rule:
                  category: natural.earthquake
                  event_type: earthquake
                  criteria:
                    all_of:
                      - key: magnitude
                        operator: gte
                        value: 4
                endpoints:
                  - email.email_primary
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "usgs_demo",
          "source": "earthquake-feed-service",
          "category": "natural.earthquake",
          "event_type": "earthquake",
          "severity": "moderate",
          "occurred_at": "2026-07-15T12:00:00Z",
          "title": "M 4.5 - Demo",
          "body": "Demo earthquake.",
          "areas": [],
          "attributes": {
            "magnitude": 4.5
          }
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "recipient_id": "platform-ops",
          "channel": "telegram",
          "endpoint_key": "ops_alerts"
        },
        {
          "recipient_id": "usr_ui",
          "channel": "email",
          "endpoint_key": "email_primary"
        }
      ]
      """

  Scenario: Ignore paused configured subscriptions
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        subscriptions:
          platform-ops:
            registry-catch-all:
              status: paused
              subscription:
                rule:
                  category: kontiki.registry
                  event_type: "*"
                  criteria:
                    all_of:
                      - key: "*"
                        operator: eq
                        value: "*"
                endpoints:
                  - telegram.ops_alerts
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "reg_any",
          "source": "kontiki-registry-alert-service",
          "category": "kontiki.registry",
          "event_type": "exception_recorded",
          "severity": "critical",
          "occurred_at": "2026-07-15T12:00:00Z",
          "title": "Registry exception",
          "body": "Unhandled exception recorded.",
          "areas": [],
          "attributes": {}
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      []
      """

  Scenario: Return recipients even when configured endpoint is not known to subscription-service
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        subscriptions:
          platform-ops:
            registry-catch-all:
              status: active
              subscription:
                rule:
                  category: kontiki.registry
                  event_type: "*"
                  criteria:
                    all_of:
                      - key: "*"
                        operator: eq
                        value: "*"
                endpoints:
                  - telegram.missing_endpoint_key
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "reg_any",
          "source": "kontiki-registry-alert-service",
          "category": "kontiki.registry",
          "event_type": "instance_state_changed",
          "severity": "low",
          "occurred_at": "2026-07-15T12:00:00Z",
          "title": "Registry state changed",
          "body": "State changed.",
          "areas": [],
          "attributes": {}
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "recipient_id": "platform-ops",
          "channel": "telegram",
          "endpoint_key": "missing_endpoint_key"
        }
      ]
      """

  Scenario: Reject invalid configured subscription at service startup
    When the subscription service fails to start with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        subscriptions:
          platform-ops:
            payment-degraded:
              status: active
              subscription:
                rule:
                  category: kontiki.registry
                  event_type: instance_state_changed
                  criteria:
                    all_of: []
                endpoints: []
      """
    Then the subscription service startup error mentions subscriptions
