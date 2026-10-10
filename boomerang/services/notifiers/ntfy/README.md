# ntfy

The ntfy notifier publishes each `NotificationRequest` for the ntfy channel to `app.ntfy.server_url`. The same image can run as an external probe for a Kontiki environment.

## Configure and run

Each endpoint needs a `topic`. `server_url` defaults to `https://ntfy.sh`. A private topic sets `app.ntfy.token` in `stack/notifiers/ntfy_token.yaml`, copied from `stack/notifiers/ntfy_token.yaml.example`, and that file is an extra `--config`. `app.ntfy.category_icons` is an optional category-to-emoji map, sent as tags. Field reference: [configuration](../../../../docs/configuration.md#ntfy-notifier-service).

### Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`.

```yaml
app:
  ntfy:
    server_url: https://ntfy.sh
  endpoints:
    alerts:
      topic: your_topic
```

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-ntfy-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/ntfy.yaml
```

From a checkout:

```bash
poetry run boomerang-ntfy-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/ntfy.yaml
```

### Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. The ntfy server must stay reachable from this process. `POST /watchdogs/{name}/heartbeat` listens on the HTTP port. Keys: [configuration](../../../../docs/configuration.md#external-sentinel-appsentinel).

```yaml
kontiki:
  amqp:
    disable: true
  http:
    address: 0.0.0.0
    port: 8006
app:
  ntfy:
    server_url: https://ntfy.sh
  endpoints:
    ops_alerts:
      topic: ops_alerts
  sentinel:
    state_path: /var/lib/boomerang/sentinel-state.json
    sweep_seconds: 10
    watchdogs:
      prod:
        token: "change-me"
        timeout_seconds: 180
        endpoint_key: ops_alerts
```

```bash
docker run --rm \
  -v "$PWD/sentinel.yaml:/sentinel.yaml:ro" \
  -v "$PWD/sentinel-state:/var/lib/boomerang" \
  -p 8006:8006 \
  ghcr.io/kontiki-org/boomerang-ntfy-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-ntfy-notifier --config sentinel.yaml
```
