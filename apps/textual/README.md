# Boomerang Textual UI

Textual client application for Boomerang.

## Structure

```text
apps/textual/
  boomerang_textual/
    app.py
    api/
      client.py
    screens/
      auth.py
      endpoints.py
      subscriptions.py
    state/
      session.py
```

## Run (local)

```bash
cd apps/textual
python -m venv .venv
source .venv/bin/activate
pip install -e .
boomerang-textual
```

