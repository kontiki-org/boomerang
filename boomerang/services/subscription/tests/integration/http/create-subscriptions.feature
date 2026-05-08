Feature: Create subscriptions with database state assertions
  In order to subscribe to relevant alerts
  As an authenticated Boomerang user
  I want to create subscriptions with predictable idempotent behavior

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

  Scenario: Persist created subscription in SQLite
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "subscription": {
            "rule": {
              "category": "weather.vigilance",
              "event_type": "thunderstorm",
              "criteria": {
                "all_of": [
                  {"key": "area.zone", "operator": "eq", "value": "FR-69"}
                ]
              }
            },
            "endpoints": [
              {"kind": "email", "endpoint_key": "email_primary"}
            ]
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
            "subscription": {
              "rule": {
                "category": "weather.vigilance",
                "event_type": "thunderstorm",
                "criteria": {
                  "all_of": [
                    {"key": "area.zone", "operator": "eq", "value": "FR-69"}
                  ]
                }
              },
              "endpoints": [
                {"kind": "email", "endpoint_key": "email_primary"}
              ]
            },
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ],
        "skipped": [],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | criteria_json                                                          | endpoints_json                                  | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | {"all_of":[{"key":"area.zone","operator":"eq","value":"FR-69"}]} | [{"kind":"email","endpoint_key":"email_primary"}] | active | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Reject payload with unknown field
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "subscription": {
            "rule": {
              "category": "weather.vigilance",
              "event_type": "thunderstorm",
              "criteria": {
                "all_of": [
                  {"key": "area.zone", "operator": "eq", "value": "FR-69"}
                ]
              },
              "unknown_field": true
            },
            "endpoints": [
              {"kind": "email", "endpoint_key": "email_primary"}
            ]
          }
        }
      }
      """
    Then the create-subscriptions call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """
