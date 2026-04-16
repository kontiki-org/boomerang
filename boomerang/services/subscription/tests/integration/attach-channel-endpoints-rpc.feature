@channel_endpoints_rpc
Feature: Attach channel endpoints via RPC
  In order to register delivery endpoints for a user
  As a provider service
  I want to attach channel endpoints via a dedicated RPC

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

  Scenario: Attach a new endpoint for a known user and channel
    Given I am authenticated as "user@example.org"
    And I have resolved the subscription user id as "[USER_ID]"
    When I call the RPC attach_channel_endpoint on the subscription service with the following arguments
      """
      {
        "user_id": "[USER_ID]",
        "channel": "email",
        "endpoint_key": "email_personal",
        "is_default": true
      }
      """
    Then the attach_channel_endpoint RPC call succeeds
    And the "channel_endpoints" table should contain
      | endpoint_id | user_id   | channel | endpoint_key    | status | is_default | created_at    | updated_at    |
      | [ANY]       | [USER_ID] | email   | email_personal  | active | 1          | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Second attach call with same key is idempotent
    Given the "channel_endpoints" table contains
      | endpoint_id | user_id   | channel | endpoint_key | status | is_default | created_at          | updated_at          |
      | ep_1        | usr_123   | sms     | sms_primary  | active | 0          | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |
    When I call the RPC attach_channel_endpoint on the subscription service with the following arguments
      """
      {
        "user_id": "usr_123",
        "channel": "sms",
        "endpoint_key": "sms_primary",
        "is_default": false
      }
      """
    Then the attach_channel_endpoint RPC call succeeds
    And the "channel_endpoints" table should contain
      | endpoint_id | user_id   | channel | endpoint_key | status | is_default | created_at          | updated_at          |
      | ep_1        | usr_123   | sms     | sms_primary  | active | 0          | 2026-01-01T00:00:00Z | 2026-01-01T00:00:00Z |

  Scenario: Reject attach when channel type is not allowed
    Given I am authenticated as "user@example.org"
    And I have resolved the subscription user id as "[USER_ID]"
    When I call the RPC attach_channel_endpoint on the subscription service with the following arguments
      """
      {
        "user_id": "[USER_ID]",
        "channel": "pigeon",
        "endpoint_key": "pigeon_1",
        "is_default": false
      }
      """
    Then the attach_channel_endpoint request is rejected due to validation error
      """
      {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request payload."
      }
      """

