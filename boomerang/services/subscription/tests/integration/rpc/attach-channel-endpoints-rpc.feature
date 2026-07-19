@channel_endpoints_rpc
Feature: Attach channel endpoints via RPC
  In order to keep subscription API coherent
  As a provider service
  I want attach_channel_endpoint to be rejected (routing now lives in subscription endpoints)

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

  Scenario: Reject attach endpoint operation
    When I call the RPC attach_channel_endpoint on the subscription service with the following arguments
      """
      {
        "user_id": "usr_example",
        "channel": "pigeon",
        "endpoint_key": "pigeon_1",
        "is_default": false
      }
      """
    Then the attach_channel_endpoint request is rejected due to validation error
      """
      {
        "code": "INTERNAL_ERROR",
        "message": "Invalid request payload."
      }
      """
