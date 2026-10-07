@telegram_watchdog
Feature: Configure watchdog heartbeats
  In order to run the telegram-notifier with or without an external watchdog
  As an operator
  I want a missing watchdog map to reject heartbeats, and an incomplete watchdog configuration to refuse to start

  No app.sentinel section: POST /watchdogs/{name}/heartbeat answers 404.
  When the section is present, state_path is required, and each endpoint_key must already exist in app.endpoints.

  Scenario: Reject a heartbeat when no watchdog is configured
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
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "123456789"
      """
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 404

  Scenario: Refuse to start without a watchdog state path
    When the telegram-notifier service fails to start with the following configuration
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
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "123456789"
        sentinel:
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: ops_alerts
      """
    Then the telegram-notifier service startup error mentions the sentinel state path

  Scenario: Refuse to start when a watchdog endpoint key is unknown
    When the telegram-notifier service fails to start with the following configuration
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
        telegram:
          bot_token: test-bot-token
          api_base_url: http://127.0.0.1:9999
        endpoints:
          ops_alerts:
            chat_id: "123456789"
        sentinel:
          state_path: /tmp/telegram-watchdog-state.json
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: missing
      """
    Then the telegram-notifier service startup error mentions the endpoint key
