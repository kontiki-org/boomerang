@email_endpoints_rpc
Feature: Bootstrap auth email endpoint via RPC
  In order to send authentication codes before a user has a session
  As identity-service
  I want email-notifier-service to create the default auth email endpoint when missing

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

  Scenario: Create auth endpoint when it does not exist
    Given I have resolved the identity user id for "user@example.org" as "[USER_ID]"
    When I call the RPC ensure_auth_email_endpoint on the email-notifier service with the following arguments
      """
      {
        "user_id": "[USER_ID]",
        "endpoint_key": "email_primary",
        "address": "user@example.org"
      }
      """
    Then the ensure_auth_email_endpoint RPC response is
      """
      {
        "endpoint": {
          "user_id": "[USER_ID]",
          "endpoint_key": "email_primary",
          "address": "user@example.org"
        }
      }
      """
    And the "email_endpoints" table should contain
      | user_id   | endpoint_key   | address          |
      | [USER_ID] | email_primary  | user@example.org |

  Scenario: Keep existing endpoint unchanged when already present
    Given the "email_endpoints" table contains
      | user_id | endpoint_key   | address               |
      | usr_123 | email_primary  | existing@example.org  |
    When I call the RPC ensure_auth_email_endpoint on the email-notifier service with the following arguments
      """
      {
        "user_id": "usr_123",
        "endpoint_key": "email_primary",
        "address": "new@example.org"
      }
      """
    Then the ensure_auth_email_endpoint RPC response is
      """
      {
        "endpoint": {
          "user_id": "usr_123",
          "endpoint_key": "email_primary",
          "address": "existing@example.org"
        }
      }
      """
    And the "email_endpoints" table should contain
      | user_id | endpoint_key   | address               |
      | usr_123 | email_primary  | existing@example.org  |

  Scenario: Reject invalid payload when required fields are missing
    When I call the RPC ensure_auth_email_endpoint on the email-notifier service with the following arguments
      """
      {
        "user_id": "",
        "endpoint_key": "email_primary",
        "address": ""
      }
      """
    Then the ensure_auth_email_endpoint request is rejected due to validation error
      """
      {
        "code": "VALIDATION_ERROR",
        "message": "Invalid request payload."
      }
      """

