@email_endpoints_http
Feature: Manage email endpoints via HTTP
  In order to manage email delivery destinations
  As an email provider service
  I want to list, retrieve and delete email endpoints over HTTP

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

  @identity_sessions_2
  Scenario: List endpoints for the authenticated user
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
    When I call GET on the email-notifier service on http://127.0.0.1:8000/email/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-email-endpoints response is
      """
      {
        "status": "ok",
        "endpoints": [
          {
            "user_id": "[USER_ID]",
            "endpoint_key": "work",
            "address": "user.work@example.org"
          }
        ]
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address               |
      | [USER_ID] | work         | user.work@example.org |

  @identity_sessions_2
  Scenario: Retrieve an endpoint by key
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
    When I call GET on the email-notifier service on http://127.0.0.1:8000/email/endpoints/work with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-email-endpoint response is
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

  @identity_sessions_3
  Scenario: Delete an endpoint
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
    When I call DELETE on the email-notifier service on http://127.0.0.1:8000/email/endpoints/work with the following request
      """
      {
        "payload": null
      }
      """
    Then the delete-email-endpoint response is
      """
      {
        "status": "ok"
      }
      """
    When I call GET on the email-notifier service on http://127.0.0.1:8000/email/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-email-endpoints response is
      """
      {
        "status": "ok",
        "endpoints": []
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address |

  @identity_sessions_1
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call GET on the email-notifier service on http://127.0.0.1:8000/email/endpoints/missing with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-email-endpoint call is rejected with HTTP 404
      """
      {
        "message": "Resource not found."
      }
      """

