@notification_endpoints_rpc
Feature: Manage notification endpoints via subscription-service RPC
  In order to manage user notification destinations from the platform
  As a trusted Boomerang client
  I want the subscription service to proxy endpoint CRUD to configured notifiers

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
  Scenario: List endpoints across configured notification channels
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
    When I call the RPC list_endpoints on the subscription service with the following arguments
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {
        "endpoints": [
          {
            "channel_id": "email",
            "user_id": "[USER_ID]",
            "endpoint_key": "work",
            "fields": {
              "address": "user.work@example.org"
            },
            "display": "user.work@example.org"
          }
        ]
      }
      """

  @identity_sessions_2
  Scenario: Retrieve an endpoint by channel and key
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
    When I call the RPC get_endpoint on the subscription service with the following arguments
      """
      {
        "channel_id": "email",
        "endpoint_key": "work",
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

  @identity_sessions_2
  Scenario: Delete an endpoint by channel and key
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
    When I call the RPC delete_endpoint on the subscription service with the following arguments
      """
      {
        "channel_id": "email",
        "endpoint_key": "work",
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {}
      """
    When I call the RPC list_endpoints on the subscription service with the following arguments
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {
        "endpoints": []
      }
      """

  @identity_sessions_2
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call the RPC get_endpoint on the subscription service with the following arguments
      """
      {
        "channel_id": "email",
        "endpoint_key": "missing",
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
