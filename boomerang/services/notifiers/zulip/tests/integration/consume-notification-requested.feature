@zulip_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing Zulip messages from the alerting pipeline
  As the zulip-notifier service
  I want to consume "zulip.alerting.notification.requested" events for the zulip channel

  Background:
    Given the zulip-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
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
          site_url: http://127.0.0.1:9997
          bot_email: boomerang-bot@example.com
          api_key: test-key
        endpoints:
          zulip_primary:
            channel: ops
            topic: alerts
      """

  Scenario: Consume a valid zulip notification request
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
            "data": {
              "category": "weather.wind",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟠 **Wind**\n\nWeather alert\n\n**Message:** Storm warning for your area."
      }
      """

  Scenario: Format a structured earthquake alert without category icons
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
        "message": {
          "title": "M 2.3 - 24 km ENE of Honey Lake, CA",
          "body": "M 2.3 - 24 km ENE of Honey Lake, CA. Detail: https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766",
          "context": {
            "kind": "alert",
            "data": {
              "alert_id": "usgs_nc75395766",
              "category": "natural.earthquake",
              "event_type": "earthquake",
              "severity": "low",
              "attributes": {
                "magnitude": 2.3,
                "place": "24 km ENE of Honey Lake, CA",
                "url": "https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766"
              }
            }
          }
        }
      }
      """
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟢 **Earthquake**\n\n**Magnitude:** 2.3\n**Place:** 24 km ENE of Honey Lake, CA\n\n🔗 [Details](https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766)"
      }
      """

  Scenario: Reject malformed notification payload
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "",
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
    Then the zulip-notifier service rejects the event as invalid payload
