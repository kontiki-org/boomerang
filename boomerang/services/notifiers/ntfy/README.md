# ntfy Notifier Service

`ntfy-notifier-service` resolves ntfy topics and delivers notifications for the
ntfy channel. With `app.sentinel`, it also holds external watchdogs and sends
a Down or Recovered alert on ntfy.

HTTP serves `POST /watchdogs/{name}/heartbeat`. Without `app.sentinel` that
route answers 404. Health in Compose stays the Kontiki registry live probe.

## What it does

- Load ntfy endpoints from YAML (`app.endpoints`).
- Expose the ntfy channel catalog (RPC `get_notification_channel_catalog`).
- Consume `ntfy.alerting.notification.requested`.
- Resolve the topic using configured `endpoint_key`.
- Format alert notifications as Markdown (shared parsing with email and
  Telegram via `notifiers.common.structured_alert`).
- Publish via JSON `POST` to the ntfy server.
- When `app.sentinel` is set, accept watchdog heartbeats and send a structured
  Down or Recovered alert on the watchdog’s endpoint.
- Mark the instance degraded on repeated publish failures (`@degraded_on`);
  alert-delivery failures surface through Kontiki exception / alerting.

## Stack

1. Copy `stack/notifiers/ntfy_token.yaml.example` to
   `stack/notifiers/ntfy_token.yaml` (gitignored) when the topic requires an
   access token:

   ```yaml
   app:
     ntfy:
       token: "tk_YOUR_ACCESS_TOKEN"
   ```

   That file is merged on top of `stack/notifiers/ntfy.yaml` at startup.
   Leave it out for an open topic on a server you trust.

2. Set `app.ntfy.server_url` in `stack/notifiers/ntfy.yaml` (default
   `https://ntfy.sh`). A self-hosted server keeps delivery on your machines.

3. Declare endpoints in `stack/notifiers/ntfy.yaml` (`app.endpoints`) and
   subscriptions (core: `stack/subscription.yaml`).

4. Start the stack:

   ```bash
   make stack-up
   ```

Events:

- consume `ntfy.alerting.notification.requested`
- publish JSON to `{server_url}/` (failures propagate as Kontiki exceptions)

## Message formatting

Alert notifications are a JSON publish:

- `title`: humanized `event_type`, or the last category segment
- `message`: Markdown attributes, then `Message:` when the body differs from
  the title
- `priority`: `low` → 2, `moderate` → 3, `severe` → 4, `critical` → 5
- `tags`: category emoji from `app.ntfy.category_icons` when one matches
- `click`: detail URL when one is available
- `markdown`: true

Non-alert messages stay plain text (`markdown` false, priority 3). Watchdog
Down and Recovered alerts use this layout (`category` `kontiki.sentinel`).

### Category icons (`app.ntfy.category_icons`)

Optional map of category key → emoji. Matching is exact, then prefix
(e.g. `weather` matches `weather.wind`). When unset or unmatched, the publish
has no tag.

See [`docs/configuration.md`](../../../../docs/configuration.md) and
[`docs/boomerang-config.example.yaml`](../../../../docs/boomerang-config.example.yaml).

## External sentinel

Optional. `POST /watchdogs/{name}/heartbeat` with `Authorization: Bearer <token>`
refreshes one watchdog. A matching token on a known name answers 204. A missing
or wrong token answers 401. An unknown name, or no `app.sentinel` section,
answers 404.

Down (`event_type` `down`, critical) and Recovered (`event_type` `recovered`,
low) are structured alerts. The attribute `watchdog` is the heartbeat name.
They go through the endpoint named by `endpoint_key`, not through the bus.

Keys and state machine: [`docs/configuration.md`](../../../../docs/configuration.md#external-sentinel-appsentinel).
