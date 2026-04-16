@alerts
Feature: List allowed alerts from configuration
  In order to create subscriptions consistently
  As a Boomerang subscription user
  I want to list only alerts allowed by service configuration

  Scenario: List configured alerts
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
            - weather.wind
            - weather.rain
            - transport.road
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/alerts with the following request
      """
      {}
      """
    Then the list-alerts response is
      """
      {
        "items": [
          "weather.wind",
          "weather.rain",
          "transport.road"
        ]
      }
      """

  Scenario: Return empty list when no alert is configured
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
    When I call GET on the subscription service on http://127.0.0.1:8000/alerts with the following request
      """
      {}
      """
    Then the list-alerts response is
      """
      {
        "items": []
      }
      """

  Scenario: Normalize configured alerts and ignore invalid entries
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
            - " Weather.Wind "
            - ""
            - "  "
            - 12
            - WEATHER.RAIN
            - "transport.road"
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/alerts with the following request
      """
      {}
      """
    Then the list-alerts response is
      """
      {
        "items": [
          "weather.wind",
          "weather.rain",
          "transport.road"
        ]
      }
      """
