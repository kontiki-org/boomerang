Feature: Update and delete subscriptions
  In order to manage an existing subscription lifecycle
  As a Boomerang subscription user
  I want to update and delete one subscription safely

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
  Scenario: Update one subscription for authenticated user
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
          {"subscription_id": "[SUB_ID]"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call PATCH on the subscription service on http://127.0.0.1:8000/subscriptions/[SUB_ID] with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "rule": {
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "criteria": {
              "all_of": [
                {"key": "severity", "operator": "eq", "value": "severe"}
              ]
            }
          },
          "endpoints": [
            {"kind": "email", "endpoint_key": "email_primary"},
            {"kind": "sms", "endpoint_key": "phone_work"}
          ],
          "status": "paused"
        }
      }
      """
    Then the update-subscription response is
      """
      {
        "status": "ok",
        "item": {
          "subscription_id": "[SUB_ID]",
          "subscription": {
            "rule": {
              "category": "weather.vigilance",
              "event_type": "thunderstorm",
              "criteria": {
                "all_of": [
                  {"key": "severity", "operator": "eq", "value": "severe"}
                ]
              }
            },
            "endpoints": [
              {"kind": "email", "endpoint_key": "email_primary"},
              {"kind": "sms", "endpoint_key": "phone_work"}
            ]
          },
          "status": "paused"
        }
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | criteria_json                                                           | endpoints_json                                                                      | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | {"all_of":[{"key":"severity","operator":"eq","value":"severe"}]} | [{"kind":"email","endpoint_key":"email_primary"},{"kind":"sms","endpoint_key":"phone_work"}] | paused | [ISO8601_UTC] | [ISO8601_UTC] |

  @identity_sessions_1
  Scenario: Delete one subscription for authenticated user
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
          {"subscription_id": "[SUB_ID]"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call DELETE on the subscription service on http://127.0.0.1:8000/subscriptions/[SUB_ID] with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the delete-subscription response is
      """
      {
        "status": "deleted"
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id | category | event_type | criteria_json | endpoints_json | status | created_at | updated_at |

  Scenario: Reject update for unknown subscription id
    Given I am authenticated as "user@example.org"
    When I call PATCH on the subscription service on http://127.0.0.1:8000/subscriptions/sub_missing with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "status": "paused"
        }
      }
      """
    Then the update-subscription call is rejected with HTTP 404
      """
      {
        "message": "Resource not found."
      }
      """

  Scenario: Reject delete for unknown subscription id
    Given I am authenticated as "user@example.org"
    When I call DELETE on the subscription service on http://127.0.0.1:8000/subscriptions/sub_missing with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the delete-subscription call is rejected with HTTP 404
      """
      {
        "message": "Resource not found."
      }
      """
