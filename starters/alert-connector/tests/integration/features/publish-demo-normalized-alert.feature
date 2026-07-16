@alert_connector_starter
Feature: Publish a pedagogical demo normalized alert
  In order to validate the starter without a business domain
  As the alert-connector-demo-service
  I want emit_demo_alert to publish one alert.normalized event

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

  Scenario: Publish a demo alert via the pedagogical RPC
    When I call the RPC emit_demo_alert on the alert connector with the following arguments
      """
      {}
      """
    Then the alert connector RPC call succeeds
    And an "alert.normalized" event is published with payload
      """
      {
        "alert_id": "demo-starter-1",
        "source": "alert-connector-demo-service",
        "category": "demo.starter",
        "event_type": "demo_alert",
        "severity": "low",
        "title": "Starter demo alert",
        "body": "Pedagogical alert from the Boomerang alert connector starter.",
        "areas": [],
        "attributes": {
          "label": "starter-demo"
        }
      }
      """
