@notification_channels_catalog_rpc
Feature: Get aggregated notification channels catalog via RPC
  In order to configure endpoints from the platform
  As a Boomerang client
  I want the subscription service to aggregate notifier channel catalogs

  Scenario: Aggregate catalogs from configured notification channels
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
        notification_channels:
          - email-notifier-service
      """
    When I call the RPC get_notification_channels_catalog on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "channels": [
          {
            "channel_id": "email",
            "label": "Email",
            "service_name": "email-notifier-service",
            "summary_field": "address",
            "fields": [
              {
                "key": "address",
                "label": "Destination",
                "field_type": "email",
                "required": true,
                "placeholder": "email address (example: user@example.org)",
                "display_in_list": true
              }
            ]
          }
        ]
      }
      """

  Scenario: Return empty catalog when no notification channel is configured
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
        notification_channels: []
      """
    When I call the RPC get_notification_channels_catalog on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "channels": []
      }
      """

  Scenario: Normalize configured notification channels and ignore invalid entries
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
        notification_channels:
          - " email-notifier-service "
          - ""
          - "  "
          - 12
      """
    When I call the RPC get_notification_channels_catalog on the subscription service with the following arguments
      """
      {}
      """
    Then the RPC call succeeds
    And the RPC response is
      """
      {
        "channels": [
          {
            "channel_id": "email",
            "label": "Email",
            "service_name": "email-notifier-service",
            "summary_field": "address",
            "fields": [
              {
                "key": "address",
                "label": "Destination",
                "field_type": "email",
                "required": true,
                "placeholder": "email address (example: user@example.org)",
                "display_in_list": true
              }
            ]
          }
        ]
      }
      """
