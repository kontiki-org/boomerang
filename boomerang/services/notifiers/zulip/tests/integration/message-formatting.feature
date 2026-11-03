@zulip_notifier_events
Feature: Zulip structured message formatting
  In order to render alerts without hardcoding domain tables
  As the zulip-notifier service
  I want category icons from configuration and automatic attribute labels

  The Zulip topic stays the configured destination. The alert title, severity icon, and category icon are part of the Markdown content.

  Scenario: Apply a category icon from configuration (exact match)
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
          category_icons:
            natural.earthquake: "🌍"
            weather: "🌧"
        endpoints:
          zulip_primary:
            channel: ops
            topic: alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🌍 🟢 **Earthquake**\n\n**Magnitude:** 2.3"
      }
      """

  Scenario: Apply a category icon from configuration (prefix match)
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
          category_icons:
            weather: "🌧"
        endpoints:
          zulip_primary:
            channel: ops
            topic: alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🌧 🟠 **Wind**\n\nWind alert\n\n**Message:** Strong winds expected."
      }
      """

  Scenario: Humanize attribute keys and keep producer insertion order
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
          zulip_primary:
            channel: ops
            topic: alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🔴 **Http**\n\n**Response Time:** 2.4s\n**Status Code:** 503\n**Service:** checkout"
      }
      """

  Scenario: Show Message body when it differs from the title even with attributes
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
          zulip_primary:
            channel: ops
            topic: alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟠 **Certificate**\n\n**Service:** api.example.com\n\n**Message:** SSL handshake failed: certificate has expired"
      }
      """

  Scenario: Banner title prefers humanized event_type over category
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
          category_icons:
            kontiki.registry: "⚙️"
        endpoints:
          zulip_primary:
            channel: ops
            topic: alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "⚙️ 🟠 **Exception Recorded**\n\n**Service Name:** demo-app-service\n\n**Message:** Uncaught exception in demo-app-service"
      }
      """
