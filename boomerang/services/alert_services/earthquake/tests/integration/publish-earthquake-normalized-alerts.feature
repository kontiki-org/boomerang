@earthquake_feed
Feature: Publish earthquake feed as normalized alerts
  In order to feed the Boomerang alerting pipeline
  As the earthquake-feed-service
  I want qualifying USGS GeoJSON features to become alert.normalized events on the bus

  Scenario: Emit alert.normalized for a new qualifying earthquake
    Given the HTTP feed mock returns GeoJSON with one new feature
      """
      {
        "type": "FeatureCollection",
        "metadata": {"generated": 1},
        "features": [
          {
            "type": "Feature",
            "properties": {
              "id": "usgs_ci_fixture_001",
              "mag": 5.0,
              "place": "Near Testville",
              "title": "M 5.0 - Near Testville",
              "time": 1710000000000,
              "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci_fixture_001"
            },
            "geometry": {
              "type": "Point",
              "coordinates": [-118.0, 34.0, 10.0]
            }
          }
        ]
      }
      """
    And the earthquake-feed-service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
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
            filename: /tmp/earthquake-feed.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        earthquake:
          usgs:
            feed_url: "http://127.0.0.1:18181/feeds/test.geojson"
          min_magnitude: 4.5
          subscription_area:
            type: "region"
            value: "DEMO-EARTHQUAKE-1"
          category: "natural.earthquake"
      """
    When the earthquake feed completes a poll cycle
    Then an "alert.normalized" event is published with payload
      """
      {
        "alert_id": "usgs_usgs_ci_fixture_001",
        "category": "natural.earthquake",
        "event_type": "earthquake",
        "severity": "moderate",
        "areas": [
          {"type": "region", "value": "DEMO-EARTHQUAKE-1"}
        ],
        "headline": "M 5.0 - Near Testville",
        "message": "M 5.0 - Near Testville. Detail: https://earthquake.usgs.gov/earthquakes/eventpage/ci_fixture_001",
        "effective_at": "2024-03-09T16:00:00Z",
        "expires_at": "2024-03-09T22:00:00Z"
      }
      """

  Scenario: Do not publish when magnitude is below the configured minimum
    Given the HTTP feed mock returns GeoJSON with one feature below min_magnitude
      """
      {
        "type": "FeatureCollection",
        "features": [
          {
            "type": "Feature",
            "properties": {
              "id": "usgs_ci_fixture_002",
              "mag": 2.0,
              "place": "Minor event",
              "title": "M 2.0 - Minor event",
              "time": 1710000000000,
              "url": "https://earthquake.usgs.gov/earthquakes/eventpage/ci_fixture_002"
            },
            "geometry": {"type": "Point", "coordinates": [-118.0, 34.0, 5.0]}
          }
        ]
      }
      """
    And the earthquake-feed-service is running with the following configuration
      """
      kontiki:
        amqp:
          url: amqp://guest:guest@localhost/
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
            filename: /tmp/earthquake-feed.log
            level: INFO
        root:
          level: DEBUG
          handlers:
            - file
      app:
        earthquake:
          usgs:
            feed_url: "http://127.0.0.1:18181/feeds/test.geojson"
          min_magnitude: 4.5
          subscription_area:
            type: "region"
            value: "DEMO-EARTHQUAKE-1"
          category: "natural.earthquake"
      """
    When the earthquake feed completes a poll cycle
    Then no "alert.normalized" event is published
