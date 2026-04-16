@recipients_rpc
Feature: Get recipients for alert via RPC
  In order to route alert deliveries to eligible users
  As the alert dispatch pipeline
  I want to resolve recipients from subscription preferences through RPC

  Background:
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
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/subscription/tests/integration/db/subscriptions.sqlite3
        channels:
          - email
          - sms
      """

  Scenario: Return matching recipient for exact area and category
    Given the "subscriptions" table contains
      | subscription_id | user_id | category     | event_type | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                               | status | created_at           | updated_at           |
      | sub_1           | usr_1   | weather.wind | *          | zone      | FR-69      | moderate     | {"channels":["email"],"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
    And the "channel_endpoints" table contains
      | endpoint_id | user_id | channel | endpoint_key  | status | is_default | created_at           | updated_at           |
      | ep_1        | usr_1   | email   | email_primary | active | 1          | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "area_type": "zone",
        "area_value": "FR-69",
        "severity": "moderate",
        "category": "weather.wind",
        "event_type": "hail"
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      [
        {
          "recipient_id": "usr_1",
          "channels": ["email"],
          "endpoint_keys": ["email_primary"]
        }
      ]
      """

  Scenario: Ignore paused subscriptions and non-matching category
    Given the "subscriptions" table contains
      | subscription_id | user_id | category     | event_type | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                               | status | created_at           | updated_at           |
      | sub_1           | usr_1   | weather.wind | *          | zone      | FR-69      | moderate     | {"channels":["email"],"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | paused | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
      | sub_2           | usr_2   | weather.rain | *          | zone      | FR-69      | moderate     | {"channels":["sms"],"fallback_to_default_channels":true}   | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
    And the "channel_endpoints" table contains
      | endpoint_id | user_id | channel | endpoint_key | status | is_default | created_at           | updated_at           |
      | ep_1        | usr_1   | email   | email_1      | active | 1          | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
      | ep_2        | usr_2   | sms     | sms_1        | active | 1          | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "area_type": "zone",
        "area_value": "FR-69",
        "severity": "severe",
        "category": "weather.wind",
        "event_type": "hail"
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      []
      """

  Scenario: Return empty list when no subscriptions match
    When I call the RPC get_recipients_for_alert on the subscription service with the following arguments
      """
      {
        "area_type": "zone",
        "area_value": "FR-69",
        "severity": "moderate",
        "category": "weather.wind",
        "event_type": "hail"
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      []
      """
