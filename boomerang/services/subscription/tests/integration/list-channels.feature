@channels
Feature: List allowed channels from configuration
  In order to configure notification destinations consistently
  As a Boomerang subscription user
  I want to list only channels allowed by service configuration

  Scenario: List configured channels
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
        channels:
          - email
          - sms
          - slack
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/channels with the following request
      """
      {}
      """
    Then the list-channels response is
      """
      {
        "items": [
          "email",
          "sms",
          "slack"
        ]
      }
      """

  Scenario: Return empty list when no channel is configured
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
        channels: []
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/channels with the following request
      """
      {}
      """
    Then the list-channels response is
      """
      {
        "items": []
      }
      """
