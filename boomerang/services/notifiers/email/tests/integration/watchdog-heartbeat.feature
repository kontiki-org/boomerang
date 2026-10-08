@email_watchdog
Feature: Heartbeat an external watchdog by email
  In order to notice when a Kontiki environment disappears
  As the email-notifier running outside that environment
  I want a stopped heartbeat to send a Down alert through the configured endpoint

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
        email:
          smtp:
            host: 127.0.0.1
            port: 1025
            use_starttls: false
            username: ""
            password: ""
          from:
            address: no-reply@example.org
        endpoints:
          ops_alerts:
            address: ops@example.org
        sentinel:
          state_path: /tmp/email-watchdog-state.json
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: ops_alerts
      """

  Scenario: Notify DOWN when heartbeats stop
    When I call POST on the email-notifier service on http://127.0.0.1:8000/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 16 seconds
    Then MailHog should contain an email matching
      """
      {
        "from": "no-reply@example.org",
        "to": ["ops@example.org"],
        "subject": "Down",
        "body_contains": [
          "Down",
          "Watchdog: prod",
          "<b>Down</b>"
        ]
      }
      """
