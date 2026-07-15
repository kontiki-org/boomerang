@notification_endpoints_rpc
Feature: Manage notification endpoints via authenticated RPC
  In order to manage notification delivery destinations
  As a trusted Boomerang service
  I want to list, retrieve and delete endpoints over authenticated RPC

  Background:
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/telegram_notifier/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
      """

  @identity_sessions_1
  Scenario: List endpoints for the authenticated user
    Given I am authenticated as "user@example.org"
    When I call the RPC create_endpoint on the telegram-notifier service with the following arguments
      """
      {
        "body": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
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
          "user_id": "[USER_ID]",
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          },
          "display": "123456789"
        }
      }
      """
    When I call the RPC list_endpoints on the telegram-notifier service with the following arguments
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
            "user_id": "[USER_ID]",
            "endpoint_key": "personal",
            "fields": {
              "chat_id": "123456789"
            },
            "display": "123456789"
          }
        ]
      }
      """
    And the "telegram_endpoints" table should contain
      | user_id   | endpoint_key | chat_id   |
      | [USER_ID] | personal     | 123456789 |

  @identity_sessions_1
  Scenario: Retrieve an endpoint by key
    Given I am authenticated as "user@example.org"
    When I call the RPC create_endpoint on the telegram-notifier service with the following arguments
      """
      {
        "body": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
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
          "user_id": "[USER_ID]",
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          },
          "display": "123456789"
        }
      }
      """
    When I call the RPC get_endpoint on the telegram-notifier service with the following arguments
      """
      {
        "endpoint_key": "personal",
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          },
          "display": "123456789"
        }
      }
      """
    And the "telegram_endpoints" table should contain
      | user_id   | endpoint_key | chat_id   |
      | [USER_ID] | personal     | 123456789 |

  @identity_sessions_1
  Scenario: Delete an endpoint
    Given I am authenticated as "user@example.org"
    When I call the RPC create_endpoint on the telegram-notifier service with the following arguments
      """
      {
        "body": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
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
          "user_id": "[USER_ID]",
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          },
          "display": "123456789"
        }
      }
      """
    When I call the RPC delete_endpoint on the telegram-notifier service with the following arguments
      """
      {
        "endpoint_key": "personal",
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the RPC response is
      """
      {}
      """
    When I call the RPC list_endpoints on the telegram-notifier service with the following arguments
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
    And the "telegram_endpoints" table should contain
      | user_id | endpoint_key | chat_id |

  @identity_sessions_1
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call the RPC get_endpoint on the telegram-notifier service with the following arguments
      """
      {
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
