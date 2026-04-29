@channels_rpc
Feature: Get allowed channels via RPC
  In order to configure notification destinations consistently
  As another Boomerang service
  I want to get only channels allowed by service configuration through RPC

  Scenario: Get configured channels via RPC
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
    When I call the RPC get_channels on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": [
          "email",
          "sms",
          "slack"
        ]
      }
      """

  Scenario: Return empty list when no channel is configured via RPC
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
    When I call the RPC get_channels on the subscription service with the following arguments
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

  Scenario: Normalize configured channels and ignore invalid entries via RPC
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
          - " Email "
          - ""
          - "  "
          - 12
          - SMS
          - "slack"
      """
    When I call the RPC get_channels on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "items": [
          "email",
          "sms",
          "slack"
        ]
      }
      """
