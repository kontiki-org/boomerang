@configured_endpoints_rpc
Feature: Configured endpoints loaded from zulip-notifier service configuration
  In order to deploy Boomerang without UI for Infrastructure-as-Code workflows
  As an operator
  I want zulip endpoints declared in service configuration to be used at notification dispatch

  Configured entries are keyed by endpoint_id (opaque, operator-chosen).
  Dispatch resolves endpoint_key against this registry.
  Each endpoint is a Zulip channel and a topic. The topic is the destination, not the alert title.
  A channel name and a topic may contain spaces. Each is at most 60 characters.

  Scenario: Deliver notification using configured endpoint
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
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟠 **State Changed**\n\nRegistry alert\n\n**Message:** payment-service degraded."
      }
      """

  Scenario: Deliver to multiple configured endpoints
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
          zulip_primary:
            channel: earth
            topic: quakes
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟢 **State Changed**\n\nOps alert\n\n**Message:** Configured endpoint delivery."
      }
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
        "endpoint_key": "zulip_primary",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "earth",
        "topic": "quakes",
        "content": "🟡 **Earthquake**\n\nUI alert\n\n**Message:** Second configured endpoint delivery."
      }
      """

  Scenario: Deliver to a channel and a topic that contain spaces
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
            channel: ops room
            topic: night alerts
      """
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
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
    Then the Zulip server should contain a message matching
      """
      {
        "type": "stream",
        "to": "ops room",
        "topic": "night alerts",
        "content": "🟠 **State Changed**\n\nRegistry alert\n\n**Message:** payment-service degraded."
      }
      """

  Scenario: Send the bot credentials as Basic authentication
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
    When an "zulip.alerting.notification.requested" event is published with payload
      """
      {
        "channel": "zulip",
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
    Then the Zulip server should contain a message matching
      """
      {
        "authorization": "Basic Ym9vbWVyYW5nLWJvdEBleGFtcGxlLmNvbTp0ZXN0LWtleQ==",
        "type": "stream",
        "to": "ops",
        "topic": "alerts",
        "content": "🟠 **Wind**\n\nWeather alert\n\n**Message:** Storm warning for your area."
      }
      """

  Scenario: Reject an endpoint with an empty channel
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
            channel: ""
            topic: alerts
      """
    Then the zulip-notifier service startup error mentions endpoints

  Scenario: Reject an endpoint with an empty topic
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
            topic: ""
      """
    Then the zulip-notifier service startup error mentions endpoints

  Scenario: Reject a channel longer than 60 characters
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
            channel: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            topic: alerts
      """
    Then the zulip-notifier service startup error mentions endpoints

  Scenario: Reject a topic longer than 60 characters
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
            topic: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      """
    Then the zulip-notifier service startup error mentions endpoints
