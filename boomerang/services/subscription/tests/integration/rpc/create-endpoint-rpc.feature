@notification_endpoints_rpc
Feature: Create or update notification endpoints via subscription-service RPC
  In order to manage user notification destinations from the platform
  As a trusted Boomerang client
  I want the subscription service to proxy endpoint creation to configured notifiers

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
        notification_channels:
          - email-notifier-service
      """

  @identity_sessions_2
  Scenario: Create a new email endpoint through the subscription service
    Given I am authenticated as "user@example.org"
    When I call the RPC create_endpoint on the subscription service with the following arguments
      """
      {
        "body": {
          "channel_id": "email",
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        },
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {
        "endpoint": {
          "channel_id": "email",
          "user_id": "[USER_ID]",
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          },
          "display": "user.work@example.org"
        }
      }
      """

  @identity_sessions_1
  Scenario: Reject endpoint creation for an unknown channel
    Given I am authenticated as "user@example.org"
    When I call the RPC create_endpoint on the subscription service with the following arguments
      """
      {
        "body": {
          "channel_id": "telegram",
          "endpoint_key": "work",
          "fields": {
            "chat_id": "-1001234567890"
          }
        },
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC request is rejected due to validation error
      """
      {
        "code": "INTERNAL_ERROR",
        "message": "Invalid request payload."
      }
      """
