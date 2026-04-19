import asyncio
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate


def _http_get_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "boomerang-earthquake-feed/0.1"})
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
    """Fetch USGS GeoJSON and map new events to ``alert.normalized`` dicts."""

    async def setup(self) -> None:
        config = self.container.config
        self._feed_url = get_parameter(
            config,
            "app.earthquake.usgs.feed_url",
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson",
        )
        self._min_magnitude = float(get_parameter(config, "app.earthquake.min_magnitude", 2.5))
        self._dedupe_max = int(get_parameter(config, "app.earthquake.dedupe_max_ids", 5000))
        self._ttl_hours = float(get_parameter(config, "app.earthquake.alert_ttl_hours", 6))
        self._http_timeout = float(get_parameter(config, "app.earthquake.http_timeout_seconds", 30))
        self._area_type = get_parameter(config, "app.earthquake.subscription_area.type", "region")
        self._area_value = get_parameter(
            config, "app.earthquake.subscription_area.value", "DEMO-EARTHQUAKE-1"
        )
        self._category = get_parameter(config, "app.earthquake.category", "natural.earthquake")
        self._seen_ids: set[str] = set()

    def _trim_dedupe(self) -> None:
        if len(self._seen_ids) > self._dedupe_max:
            self._seen_ids = set(list(self._seen_ids)[-self._dedupe_max :])

    def _feature_to_alert(self, feature: dict[str, Any]) -> dict[str, Any] | None:
        props = feature.get("properties") or {}
        usgs_id = props.get("id")
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
            return None

        place = props.get("place") or "Unknown location"
        title = props.get("title") or f"M {mag_f:.1f} — {place}"
        url = props.get("url") or ""
        time_ms = props.get("time")
        if time_ms is None:
            return None
        try:
            effective = datetime.fromtimestamp(float(time_ms) / 1000.0, tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None
        expires = effective + timedelta(hours=self._ttl_hours)

        return {
            "alert_id": f"usgs_{usgs_id}",
            "category": self._category,
            "event_type": "earthquake",
            "severity": _magnitude_to_severity(mag_f),
            "areas": [{"type": self._area_type, "value": self._area_value}],
            "headline": title,
            "message": f"{title}. Detail: {url}".strip(),
            "effective_at": effective.isoformat().replace("+00:00", "Z"),
            "expires_at": expires.isoformat().replace("+00:00", "Z"),
        }

    async def build_normalized_alerts(self) -> list[dict[str, Any]]:
        try:
            doc = await asyncio.to_thread(_http_get_json, self._feed_url, self._http_timeout)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return []

        features = doc.get("features") or []
        out: list[dict[str, Any]] = []
        for feature in features:
            if not isinstance(feature, dict):
                continue
            props = feature.get("properties") or {}
            usgs_id = props.get("id")
            if not usgs_id:
                continue
            sid = str(usgs_id)
            if sid in self._seen_ids:
                continue
            payload = self._feature_to_alert(feature)
            if payload is None:
                continue
            self._seen_ids.add(sid)
            out.append(payload)
        self._trim_dedupe()
        return out
