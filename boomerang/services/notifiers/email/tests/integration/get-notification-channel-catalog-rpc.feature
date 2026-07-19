@notification_channel_catalog_rpc
Feature: Expose email notification channel catalog via RPC
  In order to configure endpoints from the platform catalog
  As email-notifier-service
  I want to return notification channel field metadata over RPC

  Background:
    Given the email-notifier service is running with the following configuration
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
            filename: /tmp/email-notifier.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/notifiers/email/tests/integration/db/email_notifier.sqlite3
        email:
          smtp:
            host: smtp.example.org
            port: 587
            use_starttls: true
            username: smtp-user
            password: smtp-password
          from:
            address: no-reply@example.org
      """

  Scenario: Return notification channel catalog for email
    When I call the RPC get_notification_channel_catalog on the email-notifier service with the following arguments
      """
      {}
      """
    Then the RPC response is
      """
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
      """
