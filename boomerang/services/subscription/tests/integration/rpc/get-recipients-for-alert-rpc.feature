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
          usr_1:
            wind-fr69:
              status: active
              subscription:
                rule:
                  category: weather.wind
                  event_type: "*"
                  criteria:
                    all_of:
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
          "recipient_id": "usr_1",
          "channel": "email",
          "endpoint_key": "email_primary"
        }
      ]
      """

  Scenario: Ignore paused subscriptions and non-matching category
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
          usr_1:
            wind-fr69:
              status: paused
              subscription:
                rule:
                  category: weather.wind
                  event_type: "*"
                  criteria:
                    all_of:
                      - key: area.zone
                        operator: eq
                        value: FR-69
                endpoints:
                  - email.email_1
          usr_2:
            rain-fr69:
              status: active
              subscription:
                rule:
                  category: weather.rain
                  event_type: "*"
                  criteria:
                    all_of:
                      - key: area.zone
                        operator: eq
                        value: FR-69
                endpoints:
                  - sms.sms_1
      """
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "alert": {
          "schema_version": "1.0",
          "alert_id": "wx_wind_fr69_severe",
          "source": "test",
          "category": "weather.wind",
          "event_type": "hail",
          "severity": "severe",
          "occurred_at": "2026-01-15T12:00:00Z",
          "title": "Severe wind warning",
          "body": "Severe winds expected in FR-69.",
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
          usr_3:
            wind-fr75:
              status: active
              subscription:
                rule:
                  category: weather.wind
                  event_type: "*"
                  criteria:
                    all_of:
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
          "recipient_id": "usr_3",
          "channel": "email",
          "endpoint_key": "email_backup"
        }
      ]
      """
