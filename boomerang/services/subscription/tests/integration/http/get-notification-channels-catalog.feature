@notification_channels_catalog
Feature: Get aggregated notification channels catalog over HTTP
  In order to configure endpoints from the platform
  As a Boomerang subscription user
  I want to fetch the aggregated notification channels catalog over HTTP

  Scenario: Get aggregated catalog from configured notification channels
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
        notification_channels:
          - email-notifier-service
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/notification-channels/catalog with the following request
      """
      {}
      """
    Then the get-notification-channels-catalog response is
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
        notification_channels: []
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/notification-channels/catalog with the following request
      """
      {}
      """
    Then the get-notification-channels-catalog response is
      """
      {
        "channels": []
      }
      """

  Scenario: Reject the channels catalog when notification channels are not configured
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
      app: {}
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/notification-channels/catalog with the following request
      """
      {}
      """
    Then the HTTP response status is 409
    And the HTTP response is
      """
      {
        "message": "app.notification_channels is not configured"
      }
      """

  Scenario: Reject the channels catalog when notification channels are null
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
        notification_channels: null
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/notification-channels/catalog with the following request
      """
      {}
      """
    Then the HTTP response status is 409
    And the HTTP response is
      """
      {
        "message": "app.notification_channels is not configured"
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
        notification_channels:
          - " email-notifier-service "
          - ""
          - "  "
          - 12
      """
    When I call GET on the subscription service on http://127.0.0.1:8000/notification-channels/catalog with the following request
      """
      {}
      """
    Then the get-notification-channels-catalog response is
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
