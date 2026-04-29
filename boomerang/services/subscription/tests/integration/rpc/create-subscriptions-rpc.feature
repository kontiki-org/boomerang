@create_subscriptions_rpc
Feature: Create subscriptions via RPC
  In order to subscribe users from internal services
  As a trusted Boomerang service
  I want to create subscriptions through an authenticated RPC call

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

  Scenario: Persist created subscriptions through authenticated RPC
    Given I am authenticated as "user@example.org"
    When I call the RPC create_subscription on the subscription service with the following arguments
      """
      {
        "body": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": ["thunderstorm"],
            "areas": [{"type": "zone_code", "value": "FR-69"}],
            "min_severity": "moderate"
          },
          "delivery": {
            "channels": ["email"],
            "fallback_to_default_channels": true
          },
          "policy": {
            "quiet_hours": {
              "enabled": true,
              "start": "22:00",
              "end": "07:00",
              "timezone": "Europe/Paris"
            }
          }
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
        "created": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "delivery": {
              "channels": ["email"],
              "fallback_to_default_channels": true
            },
            "policy": {
              "quiet_hours": {
                "enabled": true,
                "start": "22:00",
                "end": "07:00",
                "timezone": "Europe/Paris"
              }
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
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                                              | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":["email"],"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":true,"start":"22:00","end":"07:00","timezone":"Europe/Paris"}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
