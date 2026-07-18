@alert_engine @post_alerts
Feature: Ingest normalized alerts over HTTP
  In order to submit alerts without sharing RabbitMQ
  As an external alert producer
  I want alert-engine-service to accept NormalizedAlert via POST /alerts
  and process it the same way as an alert.normalized AMQP event

  Auth is a shared secret: Authorization Bearer must match app.http.token.

  Background:
    Given the alert-engine service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8085
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
            filename: /tmp/alert-engine.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        http:
          token: "ingest-secret"
      """

  @subscription_recipients_none
  Scenario: Accept a valid alert
    When I call POST on the alert-engine service on http://127.0.0.1:8085/alerts with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer ingest-secret"
        },
        "payload": {
          "schema_version": "1.0",
          "alert_id": "al_http_1",
          "source": "external-connector",
          "category": "demo.http",
          "event_type": "ping",
          "severity": "info",
          "occurred_at": "2026-07-18T10:00:00Z",
          "title": "HTTP ingest ping",
          "body": "Ingested via POST /alerts",
          "areas": [],
          "attributes": {"label": "sandbox"}
        }
      }
      """
    Then the HTTP response status is 202
    And the HTTP response is
      """
      {
        "alert_id": "al_http_1"
      }
      """

  Scenario: Reject an invalid alert payload
    When I call POST on the alert-engine service on http://127.0.0.1:8085/alerts with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer ingest-secret"
        },
        "payload": {
          "alert_id": "",
          "source": "external-connector",
          "category": "demo.http",
          "occurred_at": "2026-07-18T10:00:00Z",
          "title": "x",
          "body": "y"
        }
      }
      """
    Then the HTTP response status is 422
    And the HTTP response is
      """
      {
        "message": "Invalid request payload."
      }
      """

  Scenario: Reject a request with a missing or invalid token
    When I call POST on the alert-engine service on http://127.0.0.1:8085/alerts with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer wrong-secret"
        },
        "payload": {
          "schema_version": "1.0",
          "alert_id": "al_http_2",
          "source": "external-connector",
          "category": "demo.http",
          "event_type": "ping",
          "severity": "info",
          "occurred_at": "2026-07-18T10:00:00Z",
          "title": "Should not ingest",
          "body": "Wrong token",
          "areas": [],
          "attributes": {}
        }
      }
      """
    Then the HTTP response status is 401
    And the HTTP response is
      """
      {
        "message": "Authentication required or invalid."
      }
      """
