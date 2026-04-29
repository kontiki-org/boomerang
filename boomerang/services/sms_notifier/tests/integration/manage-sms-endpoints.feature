@sms_endpoints_http
Feature: Manage SMS endpoints via HTTP
  In order to manage SMS delivery destinations
  As an SMS provider service
  I want to list, retrieve and delete SMS endpoints over HTTP

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

  @identity_sessions_1
  Scenario: List endpoints for the authenticated user
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
    When I call GET on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-sms-endpoints response is
      """
      {
        "status": "ok",
        "endpoints": [
          {
            "user_id": "[USER_ID]",
            "endpoint_key": "mobile",
            "phone_number": "+33612345678"
          }
        ]
      }
      """
    Then the "sms_endpoints" table should contain
      | user_id   | endpoint_key | phone_number  |
      | [USER_ID] | mobile       | +33612345678  |

  @identity_sessions_1
  Scenario: Retrieve an endpoint by key
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
    When I call GET on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints/mobile with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-sms-endpoint response is
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

  @identity_sessions_1
  Scenario: Delete an endpoint
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
    When I call DELETE on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints/mobile with the following request
      """
      {
        "payload": null
      }
      """
    Then the delete-sms-endpoint response is
      """
      {
        "status": "ok"
      }
      """
    When I call GET on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints with the following request
      """
      {
        "payload": null
      }
      """
    Then the list-sms-endpoints response is
      """
      {
        "status": "ok",
        "endpoints": []
      }
      """
    Then the "sms_endpoints" table should contain
      | user_id | endpoint_key | phone_number |

  @identity_sessions_1
  Scenario: Reject retrieval of an unknown endpoint
    Given I am authenticated as "user@example.org"
    When I call GET on the sms-notifier service on http://127.0.0.1:8000/sms/endpoints/missing with the following request
      """
      {
        "payload": null
      }
      """
    Then the get-sms-endpoint call is rejected with HTTP 404
      """
      {
        "message": "Resource not found."
      }
      """
