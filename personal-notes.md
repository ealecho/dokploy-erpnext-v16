# Personal notes — why the healthcare install works the way it does

## The core Frappe concept: bench vs site

Frappe separates **code** from **data**:

- A **bench** is the runtime: the `apps/` directory (Python/JS source of frappe, erpnext, healthcare, …), the Python virtualenv, and built assets. Apps living on the bench are just *available* code.
- A **site** is the data: one MariaDB database plus `sites/<name>/` (site_config.json, uploaded files). One bench can serve many sites (Frappe is multi-tenant by design).

Because of that split, adding an app is **two distinct operations**:

1. `bench get-app <app>` — put the app's *code* on the bench (clone, pip install, build assets). No site is touched.
2. `bench --site <site> install-app <app>` — register the app in *one site's database*: create its DocType tables, run fixtures and patches, add it to that site's `installed_apps`.

Code presence ≠ installed. A bench can carry healthcare code while only 2 of its 10 sites have it installed.

## How frappe_docker maps this onto containers

- **The image = the bench.** Code, virtualenv, and assets are baked in at build time and immutable.
- **The `sites` volume + MariaDB volume = the sites.** Only data persists across deploys.
- Every service in the compose stack — backend, queue workers, scheduler, websocket, frontend — runs **the same image**, so they all agree on what code exists.

## Why healthcare needed an image build (and `bench get-app` in a container was wrong)

Running `bench get-app` inside a running container writes code into *that one container's* writable layer:

- The other six containers never get the code. The moment the site DB says "healthcare is installed", the backend/workers that lack the code crash with `Module Healthcare not found` — the same class of error as the first-boot 500.
- On the next redeploy (`pull_policy: always`), the container is recreated from the image and the code evaporates — but the site DB still references it. Broken site.

This is the container principle of **immutable build artifacts** (12-factor: build → release → run). The image is the unit of deployment; changing what code exists means building a new image, never mutating a running container. Hence `custom-image/apps.json` + the GitHub Actions build → `ghcr.io/ealecho/erpnext-healthcare:version-16`, and `IMAGE_NAME` pointed at it so *all* services get the code atomically.

frappe_docker formalizes this: the layered `Containerfile` takes an `apps.json` and runs `bench init` at **build time** — the bench is assembled once, in CI, not on the server.

## Why `install-app` on the existing site was a manual `docker exec`

Could it happen at deploy? Partly it already does — but only for *new* sites:

- The template's `create-site` one-shot passes `INSTALL_APP_ARGS=--install-app erpnext --install-app healthcare` to `bench new-site`. Any **freshly created** site gets healthcare automatically. The job is guarded (`site exists → exit 0`), so it never touches an existing site.
- For an **existing** site, `install-app` is a one-time *state migration*: it creates tables, runs patches, and writes fixtures in that site's database. Frappe treats it as a deliberate administrative action, like `bench migrate` — not something to re-run on every deploy.

Why the template doesn't auto-install into existing sites on deploy:

1. **Multi-tenancy:** the deploy pipeline can't assume which of the bench's sites should get which app. Site-level app installation is per-site intent, not bench-level config.
2. **Risk profile:** app installation mutates schema and data. If it fails halfway during an unattended deploy, you have a half-installed app and a down site with nobody watching. Running it once, attended, with the output in front of you is the safer operational pattern.
3. **Separation of lifecycle steps:** the stack already has one-shot jobs with distinct responsibilities — `configurator` (bench config), `create-site` (new-site bootstrap), `migration` (schema migrations for already-installed apps on deploy). "Install app X into existing site Y" is a fourth, intentional step; frappe_docker upstream leaves it manual for the same reason.

It *could* be automated — `install-app` is idempotent ("App already installed") — and this template now does exactly that with an `install-apps` one-shot job (see below). That's a convenience/risk trade-off, not a technical limitation.

## The `install-apps` job: automating site convergence

The template now has a fourth one-shot job that closes the loop:

- `APPS_TO_INSTALL` (space-separated app names, e.g. `healthcare`) declares which apps every site on the bench should have. Empty (the default) means the job does nothing.
- On each deploy, after `create-site` completes, the job loops over every site directory that has a `site_config.json` and runs `bench --site <site> install-app <app>` for each declared app. Frappe skips apps that are already installed, so repeated deploys are no-ops.
- `INSTALL_APPS=0` disables the job entirely for those who prefer manual, attended installs.

This makes app installation **declarative**: `apps.json` declares what code the image carries; `APPS_TO_INSTALL` declares what every site's database should have installed. A deploy converges reality toward both declarations — the same principle as the `configurator` (bench config) and `migration` (schema) jobs.

The trade-offs accepted by turning it on:

1. It applies the same app list to *all* sites on the bench — fine for the single-site setups this template targets, wrong for true multi-tenant benches with per-site app sets.
2. A first-time install now happens during an unattended deploy. If it fails, the job exits non-zero and the failure is visible in the Dokploy deploy logs rather than in an interactive terminal.
3. Apps listed but missing from the image fail the job — which is the correct behavior, since it catches an image/app-list mismatch before it breaks the site at runtime.

## The principles in one line each

- **Bench = code, site = data** → image = code, volumes = data.
- **Available ≠ installed**: `get-app` (bench) and `install-app` (site) are different layers.
- **Immutable images**: change code by building a new image, never by mutating containers.
- **Explicit migrations**: anything that rewrites a site's database (install-app, migrate) is a deliberate lifecycle step, not an ambient side effect of deploying.
