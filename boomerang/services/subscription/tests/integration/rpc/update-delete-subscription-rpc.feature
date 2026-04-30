@update_delete_subscription_rpc
Feature: Update and delete subscriptions via RPC
  In order to manage an existing subscription lifecycle from internal services
  As a trusted Boomerang service
  I want to update and delete one subscription safely through authenticated RPC calls

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
  Scenario: Update one subscription for authenticated user via RPC
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
          {"subscription_id": "[SUB_ID]"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call the RPC update_subscription on the subscription service with the following arguments
      """
      {
        "subscription_id": "[SUB_ID]",
        "body": {
          "min_severity": "severe",
          "policy": {
            "quiet_hours": {
              "enabled": true,
              "start": "23:00",
              "end": "07:00",
              "timezone": "Europe/Paris"
            }
          },
          "status": "paused"
        },
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "status": "ok",
        "item": {
          "subscription_id": "[SUB_ID]",
          "min_severity": "severe",
          "status": "paused",
          "policy": {
            "quiet_hours": {
              "enabled": true,
              "start": "23:00",
              "end": "07:00",
              "timezone": "Europe/Paris"
            }
          }
        }
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                                                                  | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | severe       | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":true,"start":"23:00","end":"07:00","timezone":"Europe/Paris"}} | paused | [ISO8601_UTC] | [ISO8601_UTC] |

  @identity_sessions_1
  Scenario: Delete one subscription for authenticated user via RPC
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
          {"subscription_id": "[SUB_ID]"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call the RPC delete_subscription on the subscription service with the following arguments
      """
      {
        "subscription_id": "[SUB_ID]",
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "status": "deleted"
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id | category | event_type | area_type | area_value | min_severity | delivery_json | policy_json | status | created_at | updated_at |

  Scenario: Reject delete for unknown subscription id via RPC
    Given I am authenticated as "user@example.org"
    When I call the RPC delete_subscription on the subscription service with the following arguments
      """
      {
        "subscription_id": "sub_missing",
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC call fails with a NOT_FOUND_ERROR
      """
      {
        "code": "NOT_FOUND_ERROR",
        "message": "Resource not found."
      }
      """

