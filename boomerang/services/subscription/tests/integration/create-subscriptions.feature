Feature: Create subscriptions with database state assertions
  In order to subscribe to relevant alerts
  As an authenticated Boomerang user
  I want to create subscriptions with predictable idempotent behavior

  Background:
    Given the subscription service is running with the following configuration
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
            filename: /tmp/subscription.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        storage:
          backend: sqlite
          sqlite_path: boomerang/services/subscription/tests/integration/db/subscriptions.sqlite3
      """

  Scenario: Persist created subscriptions in SQLite
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": ["thunderstorm"],
            "areas": [{"type": "zone_code", "value": "FR-69"}],
            "min_severity": "moderate"
          },
          "delivery": {
            "channels": ["email"],
            "fallback_to_default_channels": true
          },
          "policy": {
            "quiet_hours": {
              "enabled": true,
              "start": "22:00",
              "end": "07:00",
              "timezone": "Europe/Paris"
            }
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "delivery": {
              "channels": ["email"],
              "fallback_to_default_channels": true
            },
            "policy": {
              "quiet_hours": {
                "enabled": true,
                "start": "22:00",
                "end": "07:00",
                "timezone": "Europe/Paris"
              }
            },
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ],
        "skipped": [],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                              | policy_json                                                                              | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":["email"],"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":true,"start":"22:00","end":"07:00","timezone":"Europe/Paris"}} | active | [ISO8601_UTC] | [ISO8601_UTC] |

  @identity_sessions_2
  Scenario: Second identical request is skipped and table state stays stable
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": ["thunderstorm"],
            "areas": [{"type": "zone_code", "value": "FR-69"}]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "delivery": {
              "channels": null,
              "fallback_to_default_channels": true
            },
            "policy": {
              "quiet_hours": {
                "enabled": false,
                "start": null,
                "end": null,
                "timezone": null
              }
            },
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ],
        "skipped": [],
        "errors": []
      }
      """
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": ["thunderstorm"],
            "areas": [{"type": "zone_code", "value": "FR-69"}]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [],
        "skipped": [
          {
            "subscription_id": "[SUB_ID]",
            "user_id": "[USER_ID]",
            "category": "weather.vigilance",
            "event_type": "thunderstorm",
            "area": {"type": "zone_code", "value": "FR-69"},
            "min_severity": "moderate",
            "delivery": {
              "channels": null,
              "fallback_to_default_channels": true
            },
            "policy": {
              "quiet_hours": {
                "enabled": false,
                "start": null,
                "end": null,
                "timezone": null
              }
            },
            "status": "active",
            "created_at": "[ISO8601_UTC]",
            "updated_at": "[ISO8601_UTC]"
          }
        ],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                         | policy_json                                                               | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Expand atomic rows for multiple alerts event types and areas
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance", "transport.traffic"],
            "event_types": ["thunderstorm"],
            "areas": [
              {"type": "zone_code", "value": "FR-69"},
              {"type": "zone_code", "value": "FR-75"}
            ]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {"subscription_id": "[SUB_ID]"},
          {"subscription_id": "[SUB_ID]"},
          {"subscription_id": "[SUB_ID]"},
          {"subscription_id": "[SUB_ID]"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type   | area_type | area_value | min_severity | delivery_json                                         | policy_json                                                               | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | thunderstorm | zone_code | FR-75      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
      | [SUB_ID]        | [USER_ID] | transport.traffic | thunderstorm | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |
      | [SUB_ID]        | [USER_ID] | transport.traffic | thunderstorm | zone_code | FR-75      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Fallback to global area when areas are omitted
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["iot.device"],
            "event_types": ["battery.low"]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {"area": {"type": "global", "value": "*"}}
        ],
        "skipped": [],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category   | event_type  | area_type | area_value | min_severity | delivery_json                                         | policy_json                                                               | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | iot.device | battery.low | global    | *          | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Empty event_types list is normalized to wildcard
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "event_types": [],
            "areas": [{"type": "zone_code", "value": "FR-69"}]
          }
        }
      }
      """
    Then the create-subscriptions response is
      """
      {
        "created": [
          {"event_type": "*"}
        ],
        "skipped": [],
        "errors": []
      }
      """
    And the "subscriptions" table should contain
      | subscription_id | user_id   | category          | event_type | area_type | area_value | min_severity | delivery_json                                         | policy_json                                                               | status | created_at    | updated_at    |
      | [SUB_ID]        | [USER_ID] | weather.vigilance | *          | zone_code | FR-69      | moderate     | {"channels":null,"fallback_to_default_channels":true} | {"quiet_hours":{"enabled":false,"start":null,"end":null,"timezone":null}} | active | [ISO8601_UTC] | [ISO8601_UTC] |

  Scenario: Reject payload with unknown field
    Given I am authenticated as "user@example.org"
    When I call POST on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        },
        "payload": {
          "selectors": {
            "categories": ["weather.vigilance"],
            "areas": [{"type": "zone_code", "value": "FR-69"}],
            "unknown_field": true
          }
        }
      }
      """
    Then the create-subscriptions call is rejected with HTTP 422
      """
      {
        "message": "Invalid request payload."
      }
      """
