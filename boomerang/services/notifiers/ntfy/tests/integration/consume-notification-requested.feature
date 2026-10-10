@ntfy_notifier_events
Feature: Consume notification delivery requests
  In order to deliver outgoing ntfy messages from the alerting pipeline
  As the ntfy-notifier service
  I want to consume "ntfy.alerting.notification.requested" events for the ntfy channel

  Background:
    Given the ntfy-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
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
          server_url: http://127.0.0.1:9998
        endpoints:
          ntfy_primary:
            topic: ops_alerts
      """

  Scenario: Consume a valid ntfy notification request
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
            "data": {
              "category": "weather.wind",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Wind",
        "message": "Weather alert\n\n**Message:** Storm warning for your area.",
        "markdown": true,
        "priority": 4
      }
      """

  Scenario: Format a structured earthquake alert without category icons
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
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
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Earthquake",
        "message": "**Magnitude:** 2.3\n**Place:** 24 km ENE of Honey Lake, CA",
        "markdown": true,
        "priority": 2,
        "click": "https://earthquake.usgs.gov/earthquakes/eventpage/nc75395766"
      }
      """

  Scenario: Reject malformed notification payload
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
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
    Then the ntfy-notifier service rejects the event as invalid payload
