@alert_connector_starter
Feature: Expose demo subscription catalog via RPC
  In order to discover starter demo alert criteria
  As the alert-connector-demo-service
  I want to return a valid AlertConnectorCatalog over RPC

  Background: Connector configuration
    Given the alert connector is running with the following configuration
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
        handlers:
          file:
            class: logging.FileHandler
            formatter: default
            filename: /tmp/alert-connector-demo.log
            level: INFO
        root:
          level: INFO
          handlers:
            - file
      app:
        demo: true
      """

  Scenario: Return subscription catalog for the starter demo
    When I call the RPC get_alert_subscription_catalog on the alert connector with the following arguments
      """
      {}
      """
    Then the alert connector RPC call succeeds
    And the alert connector RPC response is
      """
      {
        "source_id": "alert-connector-demo-service",
        "categories": [
          {
            "category": "demo.starter",
            "label": "Starter demo",
            "event_types": [
              {
                "event_type": "demo_alert",
                "label": "Demo alert",
                "criteria": [
                  {
                    "key": "label",
                    "label": "Label",
                    "operators": ["eq", "contains"],
                    "value_kind": "string",
                    "attribute_key": "label"
                  }
                ]
              }
            ]
          }
        ]
      }
      """
