@ntfy_notifier_degradation
Feature: Report degraded state for ntfy-notifier service
  In order to make service health visible in the service registry
  As an operator of the alerting platform
  I want ntfy-notifier to expose a degraded state when ntfy delivery is unhealthy

  Background:
    Given the ntfy-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        heartbeat:
          interval: 1
        http:
          address: 127.0.0.1
          port: 8006
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
            filename: /tmp/ntfy-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        ntfy:
          server_url: http://127.0.0.1:1
        endpoints:
          ntfy_primary:
            topic: ops_alerts
      """

  Scenario: Service becomes degraded after repeated ntfy failures
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    And an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    And an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {}
          }
        }
      }
      """
    Then the service registry eventually receives a heartbeat with degraded flag true
