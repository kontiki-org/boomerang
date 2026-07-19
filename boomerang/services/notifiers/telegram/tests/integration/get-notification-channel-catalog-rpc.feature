@notification_channel_catalog_rpc
Feature: Expose telegram notification channel catalog via RPC
  In order to configure endpoints from the platform catalog
  As telegram-notifier-service
  I want to return notification channel field metadata over RPC

  Background:
    Given the telegram-notifier service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
        http:
          address: 127.0.0.1
          port: 8004
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
            filename: /tmp/telegram-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/notifiers/telegram/tests/integration/db/telegram_notifier.sqlite3
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
      """

  Scenario: Return notification channel catalog for telegram
    When I call the RPC get_notification_channel_catalog on the telegram-notifier service with the following arguments
      """
      {}
      """
    Then the RPC response is
      """
      {
        "channel_id": "telegram",
        "label": "Telegram",
        "service_name": "telegram-notifier-service",
        "summary_field": "chat_id",
        "fields": [
          {
            "key": "chat_id",
            "label": "Chat ID",
            "field_type": "text",
            "required": true,
            "placeholder": "Telegram chat ID (example: 123456789)",
            "display_in_list": true
          }
        ]
      }
      """
