@zulip_watchdog
Feature: Configure watchdog heartbeats
  In order to run the zulip-notifier with or without an external watchdog
  As an operator
  I want a missing watchdog map to reject heartbeats, and an incomplete watchdog configuration to refuse to start

  No app.sentinel section: POST /watchdogs/{name}/heartbeat answers 404.
  When the section is present, state_path is required, and each endpoint_key must already exist in app.endpoints.

  Scenario: Reject a heartbeat when no watchdog is configured
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
        endpoints:
          ops_alerts:
            channel: ops
            topic: alerts
      """
    When I call POST on the zulip-notifier service on http://127.0.0.1:8007/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 404

  Scenario: Refuse to start without a watchdog state path
    When the zulip-notifier service fails to start with the following configuration
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
        endpoints:
          ops_alerts:
            channel: ops
            topic: alerts
        sentinel:
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: ops_alerts
      """
    Then the zulip-notifier service startup error mentions the sentinel state path

  Scenario: Refuse to start when a watchdog endpoint key is unknown
    When the zulip-notifier service fails to start with the following configuration
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
        endpoints:
          ops_alerts:
            channel: ops
            topic: alerts
        sentinel:
          state_path: /tmp/zulip-watchdog-state.json
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: missing
      """
    Then the zulip-notifier service startup error mentions the endpoint key
