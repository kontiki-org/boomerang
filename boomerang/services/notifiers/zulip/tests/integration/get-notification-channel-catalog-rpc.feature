@notification_channel_catalog_rpc
Feature: Expose zulip notification channel catalog via RPC
  In order to configure endpoints from the platform catalog
  As zulip-notifier-service
  I want to return notification channel field metadata over RPC

  Background:
    Given the zulip-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8007
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
            filename: /tmp/zulip-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        zulip:
          site_url: http://127.0.0.1:9997
          bot_email: boomerang-bot@example.com
          api_key: test-key
      """

  Scenario: Return notification channel catalog for zulip
    When I call the RPC get_notification_channel_catalog on the zulip-notifier service with the following arguments
      """
      {}
      """
    Then the RPC response is
      """
      {
        "channel_id": "zulip",
        "label": "Zulip",
        "service_name": "zulip-notifier-service",
        "summary_field": "channel",
        "fields": [
          {
            "key": "channel",
            "label": "Channel",
            "field_type": "text",
            "required": true,
            "placeholder": "Zulip channel (example: ops)",
            "display_in_list": true
          },
          {
            "key": "topic",
            "label": "Topic",
            "field_type": "text",
            "required": true,
            "placeholder": "Zulip topic (example: alerts)",
            "display_in_list": true
          }
        ]
      }
      """
