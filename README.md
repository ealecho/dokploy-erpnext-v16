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

## Custom apps (e.g. Healthcare)

Do **not** `bench get-app` inside a running container — only `sites/` is a persistent volume, so the app disappears on redeploy, and the other containers (backend, workers, scheduler) never get the code at all. Instead, bake apps into a custom image:

- `custom-image/apps.json` — the app list built into the image (currently ERPNext + [Marley Healthcare](https://github.com/earthians/marley), both `version-16`).
- `.github/workflows/build-image.yml` — builds the image with frappe_docker's layered `Containerfile` and pushes it to `ghcr.io/<owner>/erpnext-healthcare:version-16`. Runs on demand (`workflow_dispatch`) and whenever `custom-image/` changes.

To use it, set in the Dokploy project environment:

```
IMAGE_NAME=ghcr.io/<owner>/erpnext-healthcare
VERSION=version-16
INSTALL_APP_ARGS=--install-app erpnext --install-app healthcare
```

then redeploy. `INSTALL_APP_ARGS` only affects newly created sites. For **existing** sites, the `install-apps` one-shot job converges them on every deploy: set

```
APPS_TO_INSTALL=healthcare
```

(space-separated list of app names) and it runs `bench --site <site> install-app <app>` for every site on the bench. It is idempotent — already-installed apps are skipped — and controlled by `INSTALL_APPS=1` (set `0` to disable, e.g. if you prefer to install apps manually). Every app listed must exist in the image, or the job fails the deploy.

Alternatively, install manually once:

```bash
docker exec <backend-container> bench --site <site-name> install-app healthcare
```

## Demo seed data (Kampala clinic)

`seed/kampala_clinic_demo.py` populates a site with realistic demo data for a Ugandan clinic: 6 practitioners and 18 patients with local names, Kampala-area contact details, UGX consultation fees and lab prices, a malaria/typhoid/HIV/antenatal lab panel, common medications (Coartem, amoxicillin, …), a booked appointment calendar for today and the coming days, and past encounters with vitals, diagnoses, and prescriptions.

It is idempotent (re-runs keep existing records) and requires the setup wizard to be completed first (log in once as Administrator and finish onboarding — pick Uganda / UGX there). Then:

```bash
docker cp seed/kampala_clinic_demo.py <backend-container>:/tmp/
docker exec <backend-container> bash -c \
  "cd /home/frappe/frappe-bench/sites && ../env/bin/python /tmp/kampala_clinic_demo.py <site-name>"
```

Note: the GHCR package must be public (GitHub → Packages → package settings → change visibility), or you must add GHCR registry credentials in Dokploy.
