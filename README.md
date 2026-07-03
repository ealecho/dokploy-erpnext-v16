# Dokploy Template — ERPNext v16

A [Dokploy](https://dokploy.com) template for deploying [ERPNext](https://erpnext.com) **version 16**, based on the official [Dokploy ERPNext blueprint](https://github.com/Dokploy/templates/tree/main/blueprints/erpnext) and updated to match the current [frappe_docker](https://github.com/frappe/frappe_docker) setup.

## Contents

- `blueprints/erpnext-v16/docker-compose.yml` — full ERPNext stack: backend, nginx frontend, websocket, queue workers (default/long/short), scheduler, MariaDB 11.8, Redis cache + queue, plus one-shot `configurator`, `create-site`, and `migration` jobs.
- `blueprints/erpnext-v16/template.toml` — Dokploy variables, environment wiring, and domain mapping (routes the domain to the `frontend` service on port 8080).

## Changes vs the v15 blueprint

- Image bumped to `frappe/erpnext:version-16`.
- MariaDB `10.6` → `11.8`; dropped the `--skip-innodb-read-only-compressed` flag (removed in MariaDB 11) and switched the healthcheck to the image's built-in `healthcheck.sh`.
- Removed the unused `redis-socketio` service (socketio shares `redis-queue` since Frappe v15).
- Added `PROXY_READ_TIMEOUT` / `CLIENT_MAX_BODY_SIZE` knobs on the frontend and `--set-default` on `bench new-site`, matching upstream defaults.
- Simplified the `sites` volume to a plain named volume.
- `frontend` waits for `create-site` to complete before starting, so no traffic reaches Frappe mid-install on first boot (a request during install poisons the Redis module cache and every page 500s with "Module Website not found" until the cache is flushed). Keep `CREATE_SITE=1` — the job is idempotent and exits immediately once the site exists.

## Usage

In Dokploy, create a project → **Templates** → add this template (or paste the compose + toml into a custom template). Dokploy generates the admin and DB root passwords and assigns the domain.

First boot takes a few minutes while the site is created and ERPNext is installed. Then log in at your domain:

- **Username:** `Administrator`
- **Password:** the generated `ADMIN_PASSWORD` (see the project's Environment tab in Dokploy)
