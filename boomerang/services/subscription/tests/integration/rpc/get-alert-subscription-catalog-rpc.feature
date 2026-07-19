@alert_catalog_rpc
Feature: Get aggregated alert subscription catalog via RPC
  In order to configure subscriptions from the platform
  As a Boomerang client
  I want the subscription service to aggregate connector catalogs

  Scenario: Aggregate catalogs from configured alert connectors
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
        alert_connectors:
          - earthquake-feed-service
          - weather-alert-service
      """
    When I call the RPC get_alert_subscription_catalog on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
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

  Scenario: Return empty catalog when no alert connector is configured
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
        alert_connectors: []
      """
    When I call the RPC get_alert_subscription_catalog on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "sources": []
      }
      """
