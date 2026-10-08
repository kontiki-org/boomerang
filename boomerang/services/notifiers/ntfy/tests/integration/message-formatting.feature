@ntfy_notifier_events
Feature: ntfy structured message formatting
  In order to render alerts without hardcoding domain tables
  As the ntfy-notifier service
  I want category icons from configuration and automatic attribute labels

  Scenario: Apply a category icon from configuration (exact match)
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
          category_icons:
            natural.earthquake: "🌍"
            weather: "🌧"
        endpoints:
          ntfy_primary:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "M 2.3 - Honey Lake",
          "body": "M 2.3 - Honey Lake",
          "context": {
            "kind": "alert",
            "data": {
              "category": "natural.earthquake",
              "severity": "low",
              "attributes": {
                "magnitude": 2.3
              }
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Earthquake",
        "message": "**Magnitude:** 2.3",
        "markdown": true,
        "priority": 2,
        "tags": ["🌍"]
      }
      """

  Scenario: Apply a category icon from configuration (prefix match)
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
          category_icons:
            weather: "🌧"
        endpoints:
          ntfy_primary:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Wind alert",
          "body": "Strong winds expected.",
          "context": {
            "kind": "alert",
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
        "topic": "ops_alerts",
        "title": "Wind",
        "message": "Wind alert\n\n**Message:** Strong winds expected.",
        "markdown": true,
        "priority": 4,
        "tags": ["🌧"]
      }
      """

  Scenario: Humanize attribute keys and keep producer insertion order
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
          ntfy_primary:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Website down",
          "body": "Website down",
          "context": {
            "kind": "alert",
            "data": {
              "category": "website.http",
              "severity": "critical",
              "attributes": {
                "response_time": "2.4s",
                "status_code": 503,
                "service": "checkout"
              }
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Http",
        "message": "**Response Time:** 2.4s\n**Status Code:** 503\n**Service:** checkout",
        "markdown": true,
        "priority": 5
      }
      """

  Scenario: Show Message body when it differs from the title even with attributes
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
          ntfy_primary:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "Certificate expiry",
          "body": "SSL handshake failed: certificate has expired",
          "context": {
            "kind": "alert",
            "data": {
              "category": "certificate",
              "severity": "severe",
              "attributes": {
                "service": "api.example.com"
              }
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Certificate",
        "message": "**Service:** api.example.com\n\n**Message:** SSL handshake failed: certificate has expired",
        "markdown": true,
        "priority": 4
      }
      """

  Scenario: Banner title prefers humanized event_type over category
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
          category_icons:
            kontiki.registry: "⚙️"
        endpoints:
          ntfy_primary:
            topic: ops_alerts
      """
    When an "ntfy.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "ntfy",
        "endpoint_key": "ntfy_primary",
        "message": {
          "title": "demo-app-service exception recorded",
          "body": "Uncaught exception in demo-app-service",
          "context": {
            "kind": "alert",
            "data": {
              "category": "kontiki.registry",
              "event_type": "exception_recorded",
              "severity": "severe",
              "attributes": {
                "service_name": "demo-app-service"
              }
            }
          }
        }
      }
      """
    Then the ntfy server should contain a publish matching
      """
      {
        "topic": "ops_alerts",
        "title": "Exception Recorded",
        "message": "**Service Name:** demo-app-service\n\n**Message:** Uncaught exception in demo-app-service",
        "markdown": true,
        "priority": 4,
        "tags": ["⚙️"]
      }
      """
