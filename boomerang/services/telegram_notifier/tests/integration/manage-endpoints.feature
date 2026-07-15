@notification_endpoints_http
Feature: Manage notification endpoints via HTTP
  In order to manage notification delivery destinations
  As a notification channel service
  I want to list, retrieve and delete endpoints over HTTP

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
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          }
        }
      }
      """
    When I call GET on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-endpoints response is
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
    Then the "telegram_endpoints" table should contain
      | user_id   | endpoint_key | chat_id   |
      | [USER_ID] | personal     | 123456789 |

  @identity_sessions_1
  Scenario: Retrieve an endpoint by key
    Given I am authenticated as "user@example.org"
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          }
        }
      }
      """
    When I call GET on the telegram-notifier service on http://127.0.0.1:8004/endpoints/personal with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-endpoint response is
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
    Then the "telegram_endpoints" table should contain
      | user_id   | endpoint_key | chat_id   |
      | [USER_ID] | personal     | 123456789 |

  @identity_sessions_1
  Scenario: Delete an endpoint
    Given I am authenticated as "user@example.org"
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "123456789"
          }
        }
      }
      """
    When I call DELETE on the telegram-notifier service on http://127.0.0.1:8004/endpoints/personal with the following request
      """
      {
        "payload": null
      }
      """
    Then the delete-endpoint response is
      """
      {}
      """
    When I call GET on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-endpoints response is
      """
      {
        "endpoints": []
      }
      """
    Then the "telegram_endpoints" table should contain
      | user_id | endpoint_key | chat_id |

  @identity_sessions_1
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call GET on the telegram-notifier service on http://127.0.0.1:8004/endpoints/missing with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-endpoint call is rejected with HTTP 404
      """
      {
        "message": "Resource not found."
      }
      """
