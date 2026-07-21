@earthquake_feed
Feature: Expose earthquake subscription catalog via RPC
  In order to configure subscriptions from the platform catalog
  As the earthquake-feed-service
  I want to return alert criteria metadata over RPC

  Scenario: Return subscription catalog for earthquake alerts
    Given the earthquake-feed-service is running with the following configuration
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
            filename: /tmp/earthquake-feed.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        earthquake:
          category: "natural.earthquake"
      """
    When I call the RPC get_alert_subscription_catalog on the earthquake-feed service with the following arguments
      """
      {}
      """
    Then the earthquake-feed RPC call succeeds
    And the earthquake-feed RPC response is
      """
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
                  }
                ]
              }
            ]
          }
        ]
      }
      """
