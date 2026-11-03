@zulip_notifier_degradation
Feature: Report degraded state for zulip-notifier service
  In order to make service health visible in the service registry
  As an operator of the alerting platform
  I want zulip-notifier to expose a degraded state when Zulip delivery is unhealthy

  Background:
    Given the zulip-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        heartbeat:
          interval: 1
        http:
          address: 127.0.0.1
          port: 8007
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
            filename: /tmp/zulip-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        zulip:
          site_url: http://127.0.0.1:1
          bot_email: boomerang-bot@example.com
          api_key: test-key
        endpoints:
          zulip_primary:
            channel: ops
            topic: alerts
      """

  Scenario: Service becomes degraded after repeated Zulip failures
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    And an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    And an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
