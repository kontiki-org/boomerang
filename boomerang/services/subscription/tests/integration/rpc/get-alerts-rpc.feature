@alerts_rpc
Feature: Get allowed alerts via RPC
  In order to create subscriptions consistently
  As another Boomerang service
  I want to get only alerts allowed by service configuration through RPC

  Scenario: Get configured alerts via RPC
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
        alerts:
          allowed:
            - category: weather
              event_type: wind
            - category: weather
              event_type: rain
            - category: transport
              event_type: road
      """
    When I call the RPC get_alerts on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": [
          {"category": "weather", "event_type": "wind"},
          {"category": "weather", "event_type": "rain"},
          {"category": "transport", "event_type": "road"}
        ]
      }
      """

  Scenario: Return empty list when no alert is configured via RPC
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
        alerts:
          allowed: []
      """
    When I call the RPC get_alerts on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": []
      }
      """

  Scenario: Normalize configured alerts and ignore invalid entries via RPC
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
        alerts:
          allowed:
            - category: " Weather "
              event_type: " Wind "
            - category: ""
              event_type: "wind"
            - event_type: "wind"
            - category: 12
              event_type: "rain"
            - category: WEATHER
              event_type: RAIN
            - category: "transport"
              event_type: "road"
      """
    When I call the RPC get_alerts on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": [
          {"category": "weather", "event_type": "wind"},
          {"category": "weather", "event_type": "rain"},
          {"category": "transport", "event_type": "road"}
        ]
      }
      """
