@list-subscriptions
Feature: List subscriptions
  In order to manage my alert subscriptions
  As a Boomerang subscription user
  I want to list my subscriptions only when authenticated

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

  Scenario: Reject list-subscriptions request without bearer token
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {}
      """
    Then the list-subscriptions call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject list-subscriptions request with invalid bearer token
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer invalid-token"
        }
      }
      """
    Then the list-subscriptions call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Accept list-subscriptions request with valid bearer token
    Given I am authenticated as "user@example.org"
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the list-subscriptions response is
      """
      {
        "items": []
      }
      """

  @identity_sessions_2
  Scenario: List persisted subscriptions for authenticated user
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
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the list-subscriptions response is
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
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                   | policy_json                                                             | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
