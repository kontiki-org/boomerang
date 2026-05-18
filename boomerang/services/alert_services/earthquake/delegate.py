import asyncio
import json
import logging
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.alert_catalog import (
    AlertCategoryCatalog,
    AlertConnectorCatalog,
    AlertCriterionDescriptor,
    AlertEventTypeCatalog,
)
from boomerang.core.contracts.alert_normalized import AlertArea, NormalizedAlert
from boomerang.core.contracts.alert_services.earthquake import EARTHQUAKE_FEED_SERVICE_NAME

EARTHQUAKE_EVENT_TYPE = "earthquake"


def _http_get_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"User-Agent": "boomerang-earthquake-feed/0.1"}
    )
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        return json.loads(resp.read().decode())


def _magnitude_to_severity(mag: float) -> str:
    if mag >= 6.5:
        return "critical"
    if mag >= 5.5:
        return "severe"
    if mag >= 4.5:
        return "moderate"
    return "low"


class EarthquakeFeedDelegate(ServiceDelegate):
    """Fetch USGS GeoJSON and map new events to ``NormalizedAlert`` payloads."""

    async def setup(self) -> None:
        config = self.container.config
        self._feed_url = get_parameter(
            config,
            "app.earthquake.usgs.feed_url",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson",
        )
        self._min_magnitude = float(
            get_parameter(config, "app.earthquake.min_magnitude", 2.5)
        )
        self._dedupe_max = int(
            get_parameter(config, "app.earthquake.dedupe_max_ids", 5000)
        )
        self._ttl_hours = float(
            get_parameter(config, "app.earthquake.alert_ttl_hours", 6)
        )
        self._http_timeout = float(
            get_parameter(config, "app.earthquake.http_timeout_seconds", 30)
        )
        self._area_type = get_parameter(
            config, "app.earthquake.subscription_area.type", "region"
        )
        self._area_value = get_parameter(
            config, "app.earthquake.subscription_area.value", "DEMO-EARTHQUAKE-1"
        )
        self._category = get_parameter(
            config, "app.earthquake.category", "natural.earthquake"
        )
        self._seen_ids: set[str] = set()
        logging.info(
            "EarthquakeFeedDelegate configured feed_url=%s min_magnitude=%s category=%s "
            "area=%s/%s ttl_hours=%s dedupe_max_ids=%s",
            self._feed_url,
            self._min_magnitude,
            self._category,
            self._area_type,
            self._area_value,
            self._ttl_hours,
            self._dedupe_max,
        )

    def get_alert_subscription_catalog(self) -> AlertConnectorCatalog:
        return AlertConnectorCatalog(
            source_id=EARTHQUAKE_FEED_SERVICE_NAME,
            categories=[
                AlertCategoryCatalog(
                    category=self._category,
                    label="Earthquake",
                    event_types=[
                        AlertEventTypeCatalog(
                            event_type=EARTHQUAKE_EVENT_TYPE,
                            label="Earthquake",
                            criteria=[
                                AlertCriterionDescriptor(
                                    key="magnitude",
                                    label="Minimum magnitude",
                                    operators=["gte"],
                                    value_kind="number",
                                ),
                                AlertCriterionDescriptor(
                                    key="area.region",
                                    label="Region",
                                    operators=["eq", "contains"],
                                    value_kind="string",
                                ),
                            ],
                        )
                    ],
                )
            ],
        )

    def _trim_dedupe(self) -> None:
        if len(self._seen_ids) > self._dedupe_max:
            self._seen_ids = set(list(self._seen_ids)[-self._dedupe_max :])

    def _feature_to_alert(self, feature: dict[str, Any]) -> NormalizedAlert | None:
        props = feature.get("properties") or {}
        usgs_id = feature.get("id") or props.get("id")
        if not usgs_id:
            return None
        mag = props.get("mag")
        if mag is None:
            return None
        try:
            mag_f = float(mag)
        except (TypeError, ValueError):
            return None
        if mag_f < self._min_magnitude:
            logging.info(
                "Earthquake feed skipping feature %s with magnitude %s below minimum %s",
                usgs_id,
                mag_f,
                self._min_magnitude,
            )
            return None

        place = props.get("place") or "Unknown location"
        title = props.get("title") or f"M {mag_f:.1f} — {place}"
        url = props.get("url") or ""
        time_ms = props.get("time")
        if time_ms is None:
            return None
        try:
            occurred_at = datetime.fromtimestamp(
                float(time_ms) / 1000.0, tz=timezone.utc
            )
        except (TypeError, ValueError, OSError):
            return None
        expires_at = occurred_at + timedelta(hours=self._ttl_hours)
        body = f"{title}. Detail: {url}".strip() if url else title

        return NormalizedAlert(
            alert_id=f"usgs_{usgs_id}",
            source=EARTHQUAKE_FEED_SERVICE_NAME,
            category=self._category,
            event_type=EARTHQUAKE_EVENT_TYPE,
            severity=_magnitude_to_severity(mag_f),
            occurred_at=occurred_at,
            title=title,
            body=body,
            areas=[
                AlertArea(type=self._area_type, value=self._area_value),
            ],
            attributes={
                "magnitude": mag_f,
                "place": place,
                "url": url,
            },
            expires_at=expires_at,
        )

    async def build_normalized_alerts(self) -> list[NormalizedAlert]:
        try:
            doc = await asyncio.to_thread(
                _http_get_json, self._feed_url, self._http_timeout
            )
            logging.debug(
                "Earthquake feed HTTP/JSON fetch succeeded url=%s doc=%s",
                self._feed_url,
                doc,
            )
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            logging.warning(
                "Earthquake feed HTTP/JSON fetch failed url=%s: %s",
                self._feed_url,
                exc,
            )
            return []

        features = doc.get("features") or []
        logging.info(
            "Earthquake feed fetched %s feature(s) from %s",
            len(features),
            self._feed_url,
        )
        out: list[NormalizedAlert] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            props = feature.get("properties") or {}
            usgs_id = feature.get("id") or props.get("id")
            if not usgs_id:
                continue
            sid = str(usgs_id)
            if sid in self._seen_ids:
                continue
            alert = self._feature_to_alert(feature)
            if alert is None:
                continue
            self._seen_ids.add(sid)
            out.append(alert)
        self._trim_dedupe()
        if out:
            logging.info(
                "Earthquake feed emitting %s new alert.normalized payload(s) (seen_ids=%s)",
                len(out),
                len(self._seen_ids),
            )
        else:
            logging.info(
                "Earthquake feed poll produced no new alerts (features=%s, seen_ids=%s)",
                len(features),
                len(self._seen_ids),
            )
        return out
