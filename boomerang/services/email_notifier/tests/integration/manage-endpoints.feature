@notification_endpoints_http
Feature: Manage notification endpoints via HTTP
  In order to manage notification delivery destinations
  As a notification channel service
  I want to list, retrieve and delete endpoints over HTTP

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
  Scenario: List endpoints for the authenticated user
    Given I am authenticated as "user@example.org"
    When I call POST on the email-notifier service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call GET on the email-notifier service on http://127.0.0.1:8000/endpoints with the following request
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
            "endpoint_key": "work",
            "fields": {
              "address": "user.work@example.org"
            },
            "display": "user.work@example.org"
          }
        ]
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address               |
      | [USER_ID] | work         | user.work@example.org |

  @identity_sessions_1
  Scenario: Retrieve an endpoint by key
    Given I am authenticated as "user@example.org"
    When I call POST on the email-notifier service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call GET on the email-notifier service on http://127.0.0.1:8000/endpoints/work with the following request
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
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          },
          "display": "user.work@example.org"
        }
      }
      """
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address               |
      | [USER_ID] | work         | user.work@example.org |

  @identity_sessions_1
  Scenario: Delete an endpoint
    Given I am authenticated as "user@example.org"
    When I call POST on the email-notifier service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call DELETE on the email-notifier service on http://127.0.0.1:8000/endpoints/work with the following request
      """
      {
        "payload": null
      }
      """
    Then the delete-endpoint response is
      """
      {}
      """
    When I call GET on the email-notifier service on http://127.0.0.1:8000/endpoints with the following request
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
    Then the "email_endpoints" table should contain
      | user_id  | endpoint_key | address |

  @identity_sessions_1
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call GET on the email-notifier service on http://127.0.0.1:8000/endpoints/missing with the following request
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
