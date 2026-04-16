@email_endpoints_http
Feature: Create or update email endpoints via HTTP
  In order to deliver email notifications to the right destinations
  As an email provider service
  I want to create or update user email endpoints over HTTP

  Background:
    Given the email-notifier service is running with the following configuration
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
            filename: /tmp/email-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/email_notifier/tests/integration/db/email_notifier.sqlite3
        email:
          smtp:
            host: smtp.example.org
            port: 587
            use_starttls: true
            username: smtp-user
            password: smtp-password
          from:
            address: no-reply@example.org
      """

  Scenario: Create a new email endpoint for a user
    Given I am authenticated as "user@example.org"
    When I call POST on the email-notifier service on http://127.0.0.1:8000/email/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "work",
          "address": "user.work@example.org"
        }
      }
      """
    Then the create-email-endpoint response is
      """
      {
        "status": "ok",
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "work",
          "address": "user.work@example.org"
        }
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address               |
      | [USER_ID] | work         | user.work@example.org |

  Scenario: Second call with same user and key updates the endpoint
    Given I am authenticated as "user@example.org"
      When I call POST on the email-notifier service on http://127.0.0.1:8000/email/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "work",
          "address": "new.address@example.org"
        }
      }
      """
    Then the create-email-endpoint response is
      """
      {
        "status": "ok",
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "work",
          "address": "new.address@example.org"
        }
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address                    |
      | [USER_ID] | work         | new.address@example.org    |

  Scenario: Reject invalid payload when required fields are missing
    Given I am authenticated as "user@example.org"
    When I call POST on the email-notifier service on http://127.0.0.1:8000/email/endpoints with the following request
      """
      {
        "payload": {}
      }
      """
    Then the create-email-endpoint call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """

