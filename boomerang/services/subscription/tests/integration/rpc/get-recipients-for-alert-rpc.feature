@recipients_rpc
Feature: Get recipients for alert via RPC
  In order to route alert deliveries to eligible users
  As the alert dispatch pipeline
  I want to resolve recipients from configured subscriptions through RPC

  Scenario: Return matching recipient for exact area and category
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
          wind-fr69:
            category: weather.wind
            event_type: "*"
            criteria:
              - key: area.zone
                operator: eq
                value: FR-69
            endpoints:
              - email.email_primary
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "wx_wind_fr69",
          "source": "test",
          "category": "weather.wind",
          "event_type": "hail",
          "severity": "moderate",
          "occurred_at": "2026-01-15T12:00:00Z",
          "title": "Wind warning",
          "body": "Strong winds expected in FR-69.",
          "areas": [
            {"type": "zone", "value": "FR-69"}
          ],
          "attributes": {}
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "channel": "email",
          "endpoint_key": "email_primary"
        }
      ]
      """

  Scenario: Return empty list when no subscriptions match
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
      app: {}
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "wx_wind_fr69",
          "source": "test",
          "category": "weather.wind",
          "event_type": "hail",
          "severity": "moderate",
          "occurred_at": "2026-01-15T12:00:00Z",
          "title": "Wind warning",
          "body": "Strong winds expected in FR-69.",
          "areas": [
            {"type": "zone", "value": "FR-69"}
          ],
          "attributes": {}
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      []
      """

  Scenario: Match when criterion value exists in any area
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
          wind-fr75:
            category: weather.wind
            event_type: "*"
            criteria:
              - key: area.zone
                operator: eq
                value: FR-75
            endpoints:
              - email.email_backup
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "wx_wind_multi_zone",
          "source": "test",
          "category": "weather.wind",
          "event_type": "hail",
          "severity": "moderate",
          "occurred_at": "2026-01-15T12:00:00Z",
          "title": "Wind warning",
          "body": "Strong winds across multiple zones.",
          "areas": [
            {"type": "zone", "value": "FR-69"},
            {"type": "zone", "value": "FR-75"}
          ],
          "attributes": {}
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "channel": "email",
          "endpoint_key": "email_backup"
        }
      ]
      """

  Scenario: Return one destination when two rules match the same endpoint
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
          magnitude-moderate:
            category: natural.earthquake
            event_type: earthquake
            criteria:
              - key: magnitude
                operator: gte
                value: 4
            endpoints:
              - telegram.ops_alerts
          magnitude-severe:
            category: natural.earthquake
            event_type: earthquake
            criteria:
              - key: magnitude
                operator: gte
                value: 6
            endpoints:
              - telegram.ops_alerts
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "eq_mag_65",
          "source": "test",
          "category": "natural.earthquake",
          "event_type": "earthquake",
          "severity": "severe",
          "occurred_at": "2026-01-15T12:00:00Z",
          "title": "Earthquake",
          "body": "Magnitude 6.5.",
          "areas": [],
          "attributes": {
            "magnitude": 6.5
          }
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "channel": "telegram",
          "endpoint_key": "ops_alerts"
        }
      ]
      """
