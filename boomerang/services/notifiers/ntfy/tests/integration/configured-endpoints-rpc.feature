@configured_endpoints_rpc
Feature: Configured endpoints loaded from ntfy-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want ntfy endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen).
  Dispatch resolves endpoint_key against this registry.

  Scenario: Deliver notification using configured endpoint
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
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ops_alerts",
        "message": {
          "title": "Registry alert",
          "body": "payment-service degraded.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "state_changed",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "State Changed",
        "message": "Registry alert\n\n**Message:** payment-service degraded.",
        "markdown": true,
        "priority": 4
      }
      """

  Scenario: Deliver to multiple configured endpoints
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
            topic: ops_room
          ntfy_primary:
            topic: earth_room
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ops_alerts",
        "message": {
          "title": "Ops alert",
          "body": "Configured endpoint delivery.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "state_changed",
              "severity": "low"
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_room",
        "title": "State Changed",
        "message": "Ops alert\n\n**Message:** Configured endpoint delivery.",
        "markdown": true,
        "priority": 2
      }
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "UI alert",
          "body": "Second configured endpoint delivery.",
          "context": {
            "kind": "alert",
            "data": {
              "category": "natural.earthquake",
              "event_type": "earthquake",
              "severity": "moderate"
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "earth_room",
        "title": "Earthquake",
        "message": "UI alert\n\n**Message:** Second configured endpoint delivery.",
        "markdown": true,
        "priority": 3
      }
      """

  Scenario: Publish with the configured access token
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
          token: test-token
        endpoints:
          ops_alerts:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ops_alerts",
        "message": {
          "title": "Weather alert",
          "body": "Storm warning for your area.",
          "context": {
            "kind": "weather.alert",
            "data": {
              "category": "weather.wind",
              "severity": "severe"
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "authorization": "Bearer test-token",
        "topic": "ops_alerts",
        "title": "Wind",
        "message": "Weather alert\n\n**Message:** Storm warning for your area.",
        "markdown": true,
        "priority": 4
      }
      """

  Scenario: Reject invalid configured endpoint at service startup
    When the ntfy-notifier service fails to start with the following configuration
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
            topic: ""
      """
    Then the ntfy-notifier service startup error mentions endpoints

  Scenario: Reject a topic that ntfy would refuse
    When the ntfy-notifier service fails to start with the following configuration
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
            topic: "ops alerts"
      """
    Then the ntfy-notifier service startup error mentions endpoints
