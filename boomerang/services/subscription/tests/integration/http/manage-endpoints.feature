@notification_endpoints
Feature: Manage notification endpoints via subscription-service HTTP
  In order to manage user notification destinations from the platform
  As a Boomerang subscription user
  I want the subscription service to proxy endpoint CRUD over HTTP

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
    When I call POST on the subscription service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "channel_id": "email",
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/endpoints with the following request
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
    When I call POST on the subscription service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "channel_id": "email",
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/endpoints/email/work with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-endpoint response is
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
    When I call POST on the subscription service on http://127.0.0.1:8000/endpoints with the following request
      """
      {
        "payload": {
          "channel_id": "email",
          "endpoint_key": "work",
          "fields": {
            "address": "user.work@example.org"
          }
        }
      }
      """
    When I call DELETE on the subscription service on http://127.0.0.1:8000/endpoints/email/work with the following request
      """
      {
        "payload": null
      }
      """
    Then the delete-endpoint response is
      """
      {}
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/endpoints with the following request
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

  @identity_sessions_2
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call GET on the subscription service on http://127.0.0.1:8000/endpoints/email/missing with the following request
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
