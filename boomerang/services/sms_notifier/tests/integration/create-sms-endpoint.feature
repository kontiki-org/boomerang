@sms_endpoints_http
Feature: Create or update SMS endpoints via HTTP
  In order to deliver SMS notifications to the right destinations
  As an SMS provider service
  I want to create or update user SMS endpoints over HTTP

  Background:
    Given the sms-notifier service is running with the following configuration
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
            filename: /tmp/sms-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/sms_notifier/tests/integration/db/sms_notifier.sqlite3
        sms:
          provider:
            base_url: http://127.0.0.1:18080
            api_key: test-key
            sender_id: BOOMERANG
      """

  Scenario: Create a new SMS endpoint for a user
    Given I am authenticated as "user@example.org"
    When I call POST on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "mobile",
          "phone_number": "+33612345678"
        }
      }
      """
    Then the create-sms-endpoint response is
      """
      {
        "status": "ok",
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "mobile",
          "phone_number": "+33612345678"
        }
      }
      """
    Then the "sms_endpoints" table should contain
      | user_id   | endpoint_key | phone_number  |
      | [USER_ID] | mobile       | +33612345678  |

  Scenario: Second call with same user and key updates the endpoint
    Given I am authenticated as "user@example.org"
    When I call POST on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "mobile",
          "phone_number": "+33600000000"
        }
      }
      """
    Then the create-sms-endpoint response is
      """
      {
        "status": "ok",
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "mobile",
          "phone_number": "+33600000000"
        }
      }
      """
    Then the "sms_endpoints" table should contain
      | user_id   | endpoint_key | phone_number  |
      | [USER_ID] | mobile       | +33600000000  |

  Scenario: Reject invalid payload when required fields are missing
    Given I am authenticated as "user@example.org"
    When I call POST on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints with the following request
      """
      {
        "payload": {}
      }
      """
    Then the create-sms-endpoint call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """
