@get_subscriptions_rpc
Feature: Get subscriptions via RPC
  In order to manage user alert subscriptions from internal services
  As a trusted Boomerang service
  I want to get subscriptions for a given user id through RPC

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
      """

  @identity_sessions_1
  Scenario: Return empty list when user has no subscriptions via RPC
    Given I am authenticated as "empty@example.org"
    When I call the RPC get_subscriptions on the subscription service with the following arguments
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": []
      }
      """

  @identity_sessions_1
  Scenario: Get persisted subscriptions for a user via RPC
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": ["thunderstorm"],
            "areas": [{"type": "zone_code", "value": "FR-69"}]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call the RPC get_subscriptions on the subscription service with the following arguments
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ]
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                               | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
