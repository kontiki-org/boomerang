@alert_catalog
Feature: Get aggregated alert subscription catalog over HTTP
  In order to configure subscriptions from the platform
  As a Boomerang subscription user
  I want to fetch the aggregated alert catalog over HTTP

  Scenario: Get aggregated catalog from configured connectors
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
        alert_connectors:
          - earthquake-feed-service
          - weather-alert-service
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/alert-catalog with the following request
      """
      {}
      """
    Then the get-alert-catalog response is
      """
      {
        "sources": [
          {
            "source_id": "earthquake-feed-service",
            "categories": [
              {
                "category": "natural.earthquake",
                "label": "Earthquake",
                "event_types": [
                  {
                    "event_type": "earthquake",
                    "label": "Earthquake",
                    "criteria": [
                      {
                        "key": "magnitude",
                        "label": "Minimum magnitude",
                        "operators": ["gte"],
                        "value_kind": "number",
                        "attribute_key": "magnitude"
                      },
                      {
                        "key": "area.region",
                        "label": "Region",
                        "operators": ["eq", "contains"],
                        "value_kind": "string",
                        "attribute_key": "area.region"
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            "source_id": "weather-alert-service",
            "categories": [
              {
                "category": "weather.alert",
                "label": "Weather",
                "event_types": [
                  {
                    "event_type": "wind",
                    "label": "Wind",
                    "criteria": [
                      {
                        "key": "min_severity",
                        "label": "Minimum severity",
                        "operators": ["gte"],
                        "value_kind": "string",
                        "attribute_key": "min_severity"
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
      """

  Scenario: Return empty catalog when no connector is configured
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
        alert_connectors: []
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/alert-catalog with the following request
      """
      {}
      """
    Then the get-alert-catalog response is
      """
      {
        "sources": []
      }
      """
