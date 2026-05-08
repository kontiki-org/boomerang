@alert_engine_events
Feature: Process normalized alerts
  In order to create actionable alerts for recipients
  As the alert-engine service
  I want to process normalized events and emit channel notification requests

  Background:
    Given the alert-engine service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
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
      """

  @subscription_recipients_two
  Scenario: Emit notification request events for a normalized event with recipients
    When a "alert.normalized" event is published with payload
      """
      {
        "alert_id": "al_123",
        "category": "safety.fire",
        "event_type": "wildfire",
        "severity": "severe",
        "areas": [
          {"type": "region", "value": "REGION-1"}
        ],
        "headline": "Wildfire emergency warning",
        "message": "Evacuate affected areas immediately.",
        "effective_at": "2026-04-01T18:00:00Z",
        "expires_at": "2026-04-02T04:00:00Z"
      }
      """
    Then the alert-engine calls subscription RPC get_recipients_for_alert with
      """
      [
        "region",
        "REGION-1",
        "severe",
        "safety.fire",
        "wildfire"
      ]
      """
    When the alert-engine receives recipients from subscription RPC
      """
      [
        {
          "recipient_id": "usr_1",
          "channel": "email",
          "endpoint_key": "email_primary"
        },
        {
          "recipient_id": "usr_1",
          "channel": "sms",
          "endpoint_key": "sms_primary"
        },
        {
          "recipient_id": "usr_2",
          "channel": "sms",
          "endpoint_key": "sms_backup"
        }
      ]
      """
    Then an "email.alerting.notification.requested" event is published
      """
      {
        "channel": "email",
        "recipient_id": "usr_1",
        "endpoint_key": "email_primary",
        "message": {
          "title": "Wildfire emergency warning",
          "body": "Evacuate affected areas immediately.",
          "context": {
            "kind": "alert",
            "data": {
              "alert_id": "al_123",
              "category": "safety.fire",
              "event_type": "wildfire",
              "severity": "severe"
            }
          }
        }
      }
      """
    And a "sms.alerting.notification.requested" event is published
      """
      {
        "channel": "sms",
        "recipient_id": "usr_1",
        "endpoint_key": "sms_primary",
        "message": {
          "title": "Wildfire emergency warning",
          "body": "Evacuate affected areas immediately.",
          "context": {
            "kind": "alert",
            "data": {
              "alert_id": "al_123",
              "category": "safety.fire",
              "event_type": "wildfire",
              "severity": "severe"
            }
          }
        }
      }
      """
    And a "sms.alerting.notification.requested" event is published
      """
      {
        "channel": "sms",
        "recipient_id": "usr_2",
        "endpoint_key": "sms_backup",
        "message": {
          "title": "Wildfire emergency warning",
          "body": "Evacuate affected areas immediately.",
          "context": {
            "kind": "alert",
            "data": {
              "alert_id": "al_123",
              "category": "safety.fire",
              "event_type": "wildfire",
              "severity": "severe"
            }
          }
        }
      }
      """

  @subscription_recipients_none
  Scenario: Do not emit notification request events when no recipients match
    When a "alert.normalized" event is published with payload
      """
      {
        "alert_id": "al_456",
        "category": "infrastructure.outage",
        "event_type": "power_grid",
        "severity": "moderate",
        "areas": [
          {"type": "region", "value": "REGION-2"}
        ],
        "headline": "Power outage warning",
        "message": "Widespread outage expected in your area.",
        "effective_at": "2026-04-01T18:00:00Z",
        "expires_at": "2026-04-02T04:00:00Z"
      }
      """
    Then the alert-engine calls subscription RPC get_recipients_for_alert with
      """
      [
        "region",
        "REGION-2",
        "moderate",
        "infrastructure.outage",
        "power_grid"
      ]
      """
    When the alert-engine receives recipients from subscription RPC
      """
      []
      """
    Then no "email.alerting.notification.requested" event is published
    And no "sms.alerting.notification.requested" event is published
