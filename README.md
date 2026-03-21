# fastmvc_dashboards

**HTML dashboards for FastMVC:** FastAPI routers and shared layout/CSS for operational UIs—health, API activity, queues, tenants, secrets, workflows—and a reusable **`render_dashboard_page`** layout helper.

**Python:** 3.10+ · **Dependencies:** `fastapi`, `httpx`, `loguru`, `pydantic>=2`, `sqlalchemy>=2`

## What you get

- **Composite `DashboardRouter`** — nested routers (health, API, queues, tenants, secrets, workflows); **lazy-imported** from the package root so `fastmvc_dashboards.layout` works without the full host app on `PYTHONPATH`.
- **`layout.render_dashboard_page`**, **`BASE_CSS`** — shared HTML shell for dashboards.
- **Per-area routers** — e.g. `HealthDashboardRouter`, `ApiDashboardRouter`, … (see `src/fastmvc_dashboards/`).

> **Note:** Many sub-routers expect host app modules (`core.datastores`, `start_utils`, configurations, …). Run inside a full FastMVC app or only import submodules you need (e.g. `layout`).

## Install

```bash
pip install -e ./fastmvc_dashboards
```

## Optional dev extras

```bash
pip install -e ".[dev]"
```

## Related packages

- **`fastmvc_db`** — when dashboards query SQLAlchemy.
- Monorepo: [../README.md](../README.md).

## Tooling

See [CONTRIBUTING.md](CONTRIBUTING.md), [Makefile](Makefile), and [PUBLISHING.md](PUBLISHING.md).
