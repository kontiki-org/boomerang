@ntfy_watchdog
Feature: Heartbeat an external watchdog
  In order to notice when a Kontiki environment disappears
  As the ntfy-notifier running outside that environment
  I want an empty POST on /watchdogs/{name}/heartbeat to refresh a watchdog, and an ntfy message when it is DOWN or RECOVERED

  A known name with a matching Bearer token answers 204.
  An unknown name answers 404.
  A missing or wrong Bearer token on a known name answers 401.
  The first heartbeat marks the watchdog UP and sends nothing.
  No heartbeat, or a last heartbeat older than timeout_seconds, sends "DOWN {name}".
  A heartbeat received while DOWN sends "RECOVERED {name}".
  The state file keeps a DOWN watchdog across a restart.

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
        endpoints:
          ops_alerts:
            topic: ops_alerts
        sentinel:
          state_path: /tmp/ntfy-watchdog-state.json
          sweep_seconds: 1
          watchdogs:
            prod:
              token: secret-token
              timeout_seconds: 15
              endpoint_key: ops_alerts
      """

  Scenario: Accept a heartbeat for a known watchdog
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204

  Scenario: Reject a heartbeat with a wrong token
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer wrong-token"
        }
      }
      """
    Then the HTTP response status is 401

  Scenario: Reject a heartbeat with no token
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {}
      }
      """
    Then the HTTP response status is 401

  Scenario: Reject a heartbeat for an unknown watchdog
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/other/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 404

  Scenario: Do not notify on the first heartbeat
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the ntfy server should contain no publish

  Scenario: Notify DOWN when no heartbeat arrives
    When I wait 16 seconds
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "DOWN prod",
        "message": "DOWN prod",
        "markdown": false,
        "priority": 3
      }
      """

  Scenario: Notify DOWN when heartbeats stop, then RECOVERED when they resume
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 16 seconds
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "DOWN prod",
        "message": "DOWN prod",
        "markdown": false,
        "priority": 3
      }
      """
    When I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "RECOVERED prod",
        "message": "RECOVERED prod",
        "markdown": false,
        "priority": 3
      }
      """

  Scenario: Keep a DOWN watchdog across a restart
    When I wait 16 seconds
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "DOWN prod",
        "message": "DOWN prod",
        "markdown": false,
        "priority": 3
      }
      """
    When the ntfy-notifier service is restarted
    And I call POST on the ntfy-notifier service on http://127.0.0.1:8006/watchdogs/prod/heartbeat with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer secret-token"
        }
      }
      """
    Then the HTTP response status is 204
    When I wait 2 seconds
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "RECOVERED prod",
        "message": "RECOVERED prod",
        "markdown": false,
        "priority": 3
      }
      """
