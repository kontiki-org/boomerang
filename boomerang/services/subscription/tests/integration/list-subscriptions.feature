Feature: List subscriptions
  In order to manage my alert subscriptions
  As a Boomerang subscription user
  I want to list my subscriptions only when authenticated

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
        auth:
          auth_code:
            ttl_seconds: 30
            cooldown_seconds: 0
            rate_limit:
              max_requests: 3
              window_seconds: 5
      """

  Scenario: Reject list-subscriptions request without bearer token
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {}
      """
    Then the list-subscriptions call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Reject list-subscriptions request with invalid bearer token
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer invalid-token"
        }
      }
      """
    Then the list-subscriptions call is rejected with HTTP 401
      """
      {
        "message": "Authentication required or invalid."
      }
      """

  Scenario: Accept list-subscriptions request with valid bearer token
    Given I am authenticated as "user@example.org"
    When I call GET on the subscription service on http://127.0.0.1:8000/subscriptions with the following request
      """
      {
        "headers": {
          "Authorization": "Bearer [LAST_ACCESS_TOKEN]"
        }
      }
      """
    Then the list-subscriptions response is
      """
      {
        "items": []
      }
      """
