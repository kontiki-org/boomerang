@notification_endpoints_http
Feature: Create or update notification endpoints via HTTP
  In order to deliver notifications to the right destinations
  As a notification channel service
  I want to create or update user endpoints over HTTP

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

  Scenario: Create a new telegram endpoint for a user
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
    Then the create-endpoint response is
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

  Scenario: Second call with same user and key updates the endpoint
    Given I am authenticated as "user@example.org"
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "987654321"
          }
        }
      }
      """
    Then the create-endpoint response is
      """
      {
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "personal",
          "fields": {
            "chat_id": "987654321"
          },
          "display": "987654321"
        }
      }
      """
    Then the "telegram_endpoints" table should contain
      | user_id   | endpoint_key | chat_id   |
      | [USER_ID] | personal     | 987654321 |

  Scenario: Reject invalid payload when required fields are missing
    Given I am authenticated as "user@example.org"
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/endpoints with the following request
      """
      {
        "payload": {}
      }
      """
    Then the create-endpoint call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """
