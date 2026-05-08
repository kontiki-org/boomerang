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
      | subscription_id | user_id | category     | event_type | criteria_json                                                       | endpoints_json                                  | status | created_at           | updated_at           |
      | sub_1           | usr_1   | weather.wind | *          | {"all_of":[{"key":"area.zone","operator":"eq","value":"FR-69"}]} | [{"kind":"email","endpoint_key":"email_primary"}] | active | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
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
          "channel": "email",
          "endpoint_key": "email_primary"
        }
      ]
      """

  Scenario: Ignore paused subscriptions and non-matching category
    Given the "subscriptions" table contains
      | subscription_id | user_id | category     | event_type | criteria_json                                                       | endpoints_json                               | status | created_at           | updated_at           |
      | sub_1           | usr_1   | weather.wind | *          | {"all_of":[{"key":"area.zone","operator":"eq","value":"FR-69"}]} | [{"kind":"email","endpoint_key":"email_1"}] | paused | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
      | sub_2           | usr_2   | weather.rain | *          | {"all_of":[{"key":"area.zone","operator":"eq","value":"FR-69"}]} | [{"kind":"sms","endpoint_key":"sms_1"}]     | active | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
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
