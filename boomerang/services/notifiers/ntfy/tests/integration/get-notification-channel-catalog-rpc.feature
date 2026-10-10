@notification_channel_catalog_rpc
Feature: Expose ntfy notification channel catalog via RPC
  In order to configure endpoints from the platform catalog
  As ntfy-notifier-service
  I want to return notification channel field metadata over RPC

  Background:
    Given the ntfy-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8006
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
            filename: /tmp/ntfy-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        ntfy:
          server_url: http://127.0.0.1:9998
      """

  Scenario: Return notification channel catalog for ntfy
    When I call the RPC get_notification_channel_catalog on the ntfy-notifier service with the following arguments
      """
      {}
      """
    Then the RPC response is
      """
      {
        "channel_id": "ntfy",
        "label": "ntfy",
        "service_name": "ntfy-notifier-service",
        "summary_field": "topic",
        "fields": [
          {
            "key": "topic",
            "label": "Topic",
            "field_type": "text",
            "required": true,
            "placeholder": "ntfy topic (example: ops_alerts)",
            "display_in_list": true
          }
        ]
      }
      """
