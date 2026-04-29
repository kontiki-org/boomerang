@email_endpoints_rpc
Feature: Create or update email endpoints via authenticated RPC
  In order to allow internal services to manage user email destinations
  As a trusted Boomerang service
  I want to create or update user email endpoints over authenticated RPC

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

  @identity_sessions_1
  Scenario: Create a new email endpoint for the authenticated user via RPC
    Given I am authenticated as "user@example.org"
    When I call the RPC create_email_endpoint on the email-notifier service with the following arguments
      """
      {
        "body": {
          "endpoint_key": "work",
          "address": "user.work@example.org"
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
          "endpoint_key": "work",
          "address": "user.work@example.org"
        }
      }
      """
    And the "email_endpoints" table should contain
      | user_id   | endpoint_key | address               |
      | [USER_ID] | work         | user.work@example.org |
