# Email

The email notifier delivers each `NotificationRequest` for the email channel over SMTP. The same image can run as an external probe for a Kontiki environment.

## Configure and run

Each endpoint needs an `address`. SMTP and the From address are `app.email`. Restart the service after a change. Field reference: [configuration](../../../../docs/configuration.md#email-notifier-service).

### Standard mode

The process joins the environment bus and delivers notifications. RabbitMQ and the registry come from `stack/common.services.yaml`. The stack file points SMTP at MailHog.

```yaml
app:
  email:
    smtp:
      host: localhost
      port: 25
    from:
      address: no-reply@example.org
  endpoints:
    inbox:
      address: you@example.org
```

```bash
docker run --rm \
  -v "$PWD/stack:/stack:ro" \
  ghcr.io/kontiki-org/boomerang-email-notifier:1.0.0 \
  --config /stack/common.services.yaml \
  --config /stack/notifiers/email.yaml
```

From a checkout:

```bash
poetry run boomerang-email-notifier \
  --config stack/common.services.yaml \
  --config stack/notifiers/email.yaml
```

### Sentinel mode

The process runs outside the environment and watches its heartbeats. Silence (hosts or RabbitMQ down) sends Down on this channel; the next heartbeat sends Recovered. `kontiki.amqp.disable: true` keeps startup independent of that environment's broker. SMTP must stay reachable from this process. `POST /watchdogs/{name}/heartbeat` listens on the HTTP port. Keys: [configuration](../../../../docs/configuration.md#external-sentinel-appsentinel).

```yaml
kontiki:
  amqp:
    disable: true
  http:
    address: 0.0.0.0
    port: 8003
app:
  email:
    smtp:
      host: localhost
      port: 25
    from:
      address: no-reply@example.org
  endpoints:
    ops_alerts:
      address: ops@example.org
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
  -p 8003:8003 \
  ghcr.io/kontiki-org/boomerang-email-notifier:1.0.0 \
  --config /sentinel.yaml
```

From a checkout:

```bash
poetry run boomerang-email-notifier --config sentinel.yaml
```
