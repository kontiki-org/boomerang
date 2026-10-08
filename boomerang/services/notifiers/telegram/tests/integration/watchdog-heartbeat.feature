@telegram_watchdog
Feature: Heartbeat an external watchdog
  In order to notice when a Kontiki environment disappears
  As the telegram-notifier running outside that environment
  I want an empty POST on /watchdogs/{name}/heartbeat to refresh a watchdog, and a Telegram message when it is DOWN or RECOVERED

  A known name with a matching Bearer token answers 204.
  An unknown name answers 404.
  A missing or wrong Bearer token on a known name answers 401.
  The first heartbeat marks the watchdog UP and sends nothing.
  No heartbeat, or a last heartbeat older than timeout_seconds, sends a Down alert for that watchdog.
  A heartbeat received while DOWN sends a Recovered alert for that watchdog.
  The state file keeps a DOWN watchdog across a restart.

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
              endpoint_key: ops_alerts
      """

  Scenario: Accept a heartbeat for a known watchdog
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204

  Scenario: Reject a heartbeat with a wrong token
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer wrong-token"
        }
      }
      """
    Then the HTTP response status is 401

  Scenario: Reject a heartbeat with no token
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {}
      }
      """
    Then the HTTP response status is 401

  Scenario: Reject a heartbeat for an unknown watchdog
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/other/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 404

  Scenario: Do not notify on the first heartbeat
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the Telegram API should contain no sendMessage

  Scenario: Notify DOWN when no heartbeat arrives
    When I wait 16 seconds
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🔴 <b>Down</b>\n\n<b>Watchdog:</b> prod",
        "parse_mode": "HTML"
      }
      """

  Scenario: Notify DOWN when heartbeats stop, then RECOVERED when they resume
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 16 seconds
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🔴 <b>Down</b>\n\n<b>Watchdog:</b> prod",
        "parse_mode": "HTML"
      }
      """
    When I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🟢 <b>Recovered</b>\n\n<b>Watchdog:</b> prod",
        "parse_mode": "HTML"
      }
      """

  Scenario: Keep a DOWN watchdog across a restart
    When I wait 16 seconds
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🔴 <b>Down</b>\n\n<b>Watchdog:</b> prod",
        "parse_mode": "HTML"
      }
      """
    When the telegram-notifier service is restarted
    And I call POST on the telegram-notifier service on http://127.0.0.1:8004/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the Telegram API should contain a sendMessage matching
      """
      {
        "chat_id": "123456789",
        "text": "🟢 <b>Recovered</b>\n\n<b>Watchdog:</b> prod",
        "parse_mode": "HTML"
      }
      """
