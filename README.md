# fast_dashboards

**HTML dashboards for FastMVC:** FastAPI routers and shared layout/CSS for operational UIs—health, API activity, queues, tenants, secrets, workflows—and a reusable **`render_dashboard_page`** layout helper. Also **signed embed URLs** (time-limited HMAC) and **Metabase / Grafana** embed helpers behind one protocol.

**Python:** 3.10+ · **Dependencies:** `fastapi`, `httpx`, `loguru`, `pydantic>=2`, `sqlalchemy>=2` · **Optional:** `PyJWT` for Metabase (`pip install 'fast_dashboards[metabase]'`).

## What you get

- **`sign_embed_url`**, **`verify_signed_embed_url`** — append `exp` + `sig` (HMAC-SHA256) for iframe-safe dashboard URLs; optional signed **`tid`** (revocation id), **`theme`**, **`locale`** query params.
- **`EmbedRevocationChecker`**, **`InMemoryEmbedRevocationList`** — block leaked embeds by revoking **`tid`** before expiry.
- **`EmbedThemeParams`**, **`theme_to_extra_params`** — bundle dark/light + locale for **`sign_embed_url`** / Grafana.
- **`DashboardEmbedProvider`**, **`MetabaseEmbedProvider`**, **`GrafanaEmbedProvider`** — unified `build_embed_url(resource_id=..., ttl_seconds=...)`; Grafana supports **`theme`** / **`locale`** / **`token_id`**; Metabase supports **`theme`** (URL fragment) and **`locale`** (JWT params).
- **`LookerEmbedProvider`**, **`PowerBIEmbedProvider`** — stubs; use Looker Signed Embed / Power BI **GenerateToken** (see below).
- **Composite `DashboardRouter`** — nested routers (health, API, queues, tenants, secrets, workflows); **lazy-imported** from the package root so `fast_dashboards.layout` works without the full host app on `PYTHONPATH`.
- **`layout.render_dashboard_page`**, **`BASE_CSS`** — shared HTML shell for dashboards with **production SEO** (Open Graph, Twitter Card, canonical URL when `FASTMVC_PUBLIC_BASE_URL` is set, JSON-LD `WebPage` + `SoftwareApplication`, `theme-color`, safe **`noindex, nofollow`** defaults for internal ops UIs).
- **`core.seo`** — `PageSEO`, `render_seo_head`, `render_dashboard_inline_head`, and `robots_txt_*` helpers for public sites vs private dashboards.
- **Per-area routers** — e.g. `HealthDashboardRouter`, `ApiDashboardRouter`, … (see `src/fast_dashboards/`).

> **Note:** Many sub-routers expect host app modules (`core.datastores`, `start_utils`, configurations, …). Run inside a full FastMVC app or only import submodules you need (e.g. `layout`, `embed_signing`, `providers`).

> **Core vs dashboards:** Generic “platform” building blocks that used to live under `fast_dashboards.core` (auth, tracing, encryption, smart cache, saga, etc.) are implemented in **`fast-platform`** under `fast_platform.core` (and `fast_platform.caching`). `fast_dashboards.core` still re-exports them for compatibility; prefer `from fast_platform.core…` in new code. Dashboard-only pieces remain here (`layout`, `router`, embed signing/theme/SEO, …).

## Looker (recipe)

Looker **Signed embed** uses a server-generated SSO URL per session. Implement a small service that calls Looker’s API with your embed secret, then pass the returned URL to the iframe. Do **not** expect a static `build_embed_url` from this package — **`LookerEmbedProvider`** is a deliberate stub.

## Power BI (recipe)

Use the Power BI REST API **GenerateToken** for reports/dashboards (Azure AD app registration). Return the embed URL + token to the client per Microsoft’s embed flow. **`PowerBIEmbedProvider`** is a stub pointing you to that flow.

## Revocation example

```python
from fast_dashboards import InMemoryEmbedRevocationList, sign_embed_url, verify_signed_embed_url

secret = b"your-32-byte-secret-here!!!!"
block = InMemoryEmbedRevocationList()
url = sign_embed_url("https://dash.example.com/view", secret, 3600, token_id="session-abc")
# Later: leak detected
block.revoke("session-abc")
assert verify_signed_embed_url(url, secret, revocation=block) is None
```

## Install

```bash
pip install -e ./fast_dashboards
```

## Optional dev extras

```bash
pip install -e ".[dev]"
```

## Related packages

- **`fast_db`** — when dashboards query SQLAlchemy.
- Monorepo: [../README.md](../README.md).

## Tooling

See [CONTRIBUTING.md](CONTRIBUTING.md), [Makefile](Makefile), and [PUBLISHING.md](PUBLISHING.md).

---

## Documentation

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, tests, monorepo sync |
| [PUBLISHING.md](PUBLISHING.md) | PyPI and releases |
| [SECURITY.md](SECURITY.md) | Reporting vulnerabilities |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

**Monorepo:** [../README.md](../README.md) · **Coverage:** [../docs/COVERAGE.md](../docs/COVERAGE.md)
