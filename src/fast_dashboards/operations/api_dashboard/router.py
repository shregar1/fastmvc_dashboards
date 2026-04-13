"""API Activity Dashboard Router.

Provides a built-in dashboard similar in spirit to /docs and /redoc that
shows configured APIs along with sample payloads and lets you exercise
them from the UI to see whether they are active.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from fast_dashboards.core.constants import (
    DEFAULT_SITE_NAME,
    LOCALSTORAGE_THEME_KEY_API,
    MAX_BODY_PREVIEW_LENGTH,
    MAX_ERROR_LENGTH,
    REQUEST_TIMEOUT_SECONDS,
    ROUTER_PREFIX_API,
    HTTP_STATUS_SERVER_ERROR_THRESHOLD,
)
from ...core.seo import render_dashboard_inline_head

from .registry import EndpointSample, get_endpoint_sample, list_endpoint_samples


router = APIRouter(prefix=ROUTER_PREFIX_API, tags=["API Dashboard"])


def _serialize_sample(sample: EndpointSample) -> Dict[str, Any]:
    """Execute _serialize_sample operation.

    Args:
        sample: The sample parameter.

    Returns:
        The result of the operation.
    """
    return {
        "key": sample.key,
        "name": sample.name,
        "method": sample.method,
        "path": sample.path,
        "description": sample.description,
        "sampleRequest": sample.sample_request or {},
        "sampleQuery": sample.sample_query or {},
        "enabled": sample.enabled,
    }


@router.get("", response_class=HTMLResponse, summary="API Activity Dashboard")
async def api_dashboard() -> HTMLResponse:
    """Render the API dashboard page.

    The page fetches live data from the same router's JSON endpoints to
    keep the backend logic simple and avoid static assets.
    """
    _head_seo = render_dashboard_inline_head(
        page_title=f"{DEFAULT_SITE_NAME} API Dashboard",
        description="Explore registered API endpoints, sample payloads, and live probes from the FastMVC API dashboard.",
        path=ROUTER_PREFIX_API,
    )
    html = (
        """
<!DOCTYPE html>
<html lang="en">
  <head>
    """
        + _head_seo
        + """
    <style>
      :root {
        --bg: #0a0a0b;
        --surface: #141416;
        --surface-raised: #1c1c1f;
        --border: #27272a;
        --border-hover: #3f3f46;
        --text: #fafafa;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --accent: #e4e4e7;
        --success: #22c55e;
        --warning: #eab308;
        --error: #ef4444;
        --info: #3b82f6;
        --method-get: #3b82f6;
        --method-post: #22c55e;
        --method-put: #eab308;
        --method-delete: #ef4444;
        --method-patch: #8b5cf6;
      }

      [data-theme="light"] {
        --bg: #fafafa;
        --surface: #ffffff;
        --surface-raised: #f4f4f5;
        --border: #e4e4e7;
        --border-hover: #d4d4d8;
        --text: #18181b;
        --text-secondary: #52525b;
        --text-muted: #a1a1aa;
        --accent: #18181b;
        --success: #16a34a;
        --warning: #ca8a04;
        --error: #dc2626;
        --info: #2563eb;
        --method-get: #2563eb;
        --method-post: #16a34a;
        --method-put: #ca8a04;
        --method-delete: #dc2626;
        --method-patch: #7c3aed;
      }

      * { box-sizing: border-box; }

      html, body {
        margin: 0;
        min-height: 100vh;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: var(--bg);
        color: var(--text);
        transition: background 0.3s ease, color 0.3s ease;
      }

      .container {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 32px 16px;
      }

      .card {
        width: 100%;
        max-width: 1160px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
      }

      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
        flex-wrap: wrap;
      }

      .header-main {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }

      .title {
        font-size: 1.5rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .subtitle {
        font-size: 0.92rem;
        color: var(--text-secondary);
      }

      .badge {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        background: var(--surface-raised);
        border: 1px solid var(--border);
        color: var(--text-secondary);
        font-weight: 600;
      }

      .header-right {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }

      .pill {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        background: var(--surface-raised);
        border: 1px solid var(--border);
        color: var(--text-muted);
      }

      .theme-toggle {
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 6px;
        cursor: pointer;
        color: var(--text-secondary);
        transition: all 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .theme-toggle:hover {
        background: var(--border);
        border-color: var(--border-hover);
        color: var(--text);
      }

      .theme-toggle svg { width: 18px; height: 18px; }
      .theme-toggle .sun { display: none; }
      .theme-toggle .moon { display: block; }
      [data-theme="light"] .theme-toggle .sun { display: block; }
      [data-theme="light"] .theme-toggle .moon { display: none; }

      .grid {
        display: grid;
        grid-template-columns: minmax(0, 2.1fr) minmax(0, 2.5fr);
        gap: 16px;
      }

      @media (max-width: 900px) {
        .grid { grid-template-columns: 1fr; }
      }

      .list-card, .detail-card {
        background: var(--surface-raised);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 12px;
        min-height: 220px;
        transition: all 0.3s ease;
      }

      .list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }

      .list-title {
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text);
      }

      .list-body {
        max-height: 360px;
        overflow-y: auto;
      }

      .endpoint-row {
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.15s ease;
        margin-bottom: 6px;
        background: var(--surface);
        border: 1px solid var(--border);
      }

      .endpoint-row:hover {
        border-color: var(--border-hover);
        transform: translateY(-1px);
      }

      .endpoint-row.active {
        background: var(--surface);
        border-color: var(--text-muted);
      }

      .method-pill {
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
        font-family: ui-monospace, monospace;
      }

      .method-get { background: var(--method-get); color: white; }
      .method-post { background: var(--method-post); color: white; }
      .method-put { background: var(--method-put); color: white; }
      .method-patch { background: var(--method-patch); color: white; }
      .method-delete { background: var(--method-delete); color: white; }

      .endpoint-main {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .endpoint-name {
        font-size: 0.86rem;
        font-weight: 500;
        color: var(--text);
      }

      .endpoint-path {
        font-size: 0.78rem;
        color: var(--text-muted);
        font-family: ui-monospace, SFMono-Regular, monospace;
      }

      .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--text-muted);
      }

      .status-dot.ok { background: var(--success); }
      .status-dot.error { background: var(--error); }

      .detail-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
      }

      .detail-title {
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text);
      }

      .badge-soft {
        padding: 4px 12px;
        font-size: 0.75rem;
        border-radius: 6px;
        background: var(--surface);
        border: 1px solid var(--border);
        color: var(--text-secondary);
      }

      .detail-body {
        display: grid;
        grid-template-rows: auto 1fr auto;
        gap: 12px;
      }

      .detail-meta {
        font-size: 0.875rem;
        color: var(--text-secondary);
      }

      .code-block {
        position: relative;
        background: var(--bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
        font-size: 0.8rem;
        font-family: ui-monospace, SFMono-Regular, monospace;
        color: var(--text);
        overflow: auto;
      }

      .code-block pre {
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
      }

      .detail-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
      }

      .btn {
        border: none;
        outline: none;
        cursor: pointer;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 0.85rem;
        font-weight: 600;
        background: var(--text);
        color: var(--bg);
        transition: all 0.15s ease;
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .btn:hover:not(:disabled) {
        background: var(--accent);
      }

      .status-text {
        font-size: 0.875rem;
        color: var(--text-muted);
      }

      .status-text.ok { color: var(--success); }
      .status-text.error { color: var(--error); }

      ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
      }

      ::-webkit-scrollbar-track {
        background: var(--surface);
      }

      ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 3px;
      }

      ::-webkit-scrollbar-thumb:hover {
        background: var(--border-hover);
      }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <header class="header">
          <div class="header-main">
            <div class="title">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--text);">
                <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/>
                <polyline points="12 22 12 15.5"/>
                <polyline points="22 8.5 12 15.5 2 8.5"/>
              </svg>
              API Activity
              <span class="badge">FastMVC dashboard</span>
            </div>
            <p class="subtitle">
              Configure sample requests for your endpoints and run live checks
              to see which APIs are active and healthy.
            </p>
          </div>
          <div class="header-right">
            <span class="pill">Mode: Dashboard</span>
            <span class="pill">Source: In-memory registry</span>
            <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
              <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
              <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            </button>
          </div>
        </header>

        <section class="grid">
          <article class="list-card">
            <div class="list-header">
              <div class="list-title">Endpoints</div>
              <div id="endpoint-count" class="badge-soft">Loading…</div>
            </div>
            <div class="list-body" id="endpoint-list"></div>
          </article>

          <article class="detail-card">
            <div class="detail-title-row">
              <div class="detail-title">Details</div>
              <div id="detail-method-pill" class="badge-soft" style="display:none;"></div>
            </div>
            <div class="detail-body">
              <div class="detail-meta" id="detail-meta">
                Select an endpoint on the left to see its sample payload
                and run a live health request.
              </div>
              <div class="code-block">
                <pre id="detail-sample">{}</pre>
              </div>
              <div class="detail-footer">
                <button class="btn" id="btn-run" disabled>Run sample</button>
                <div class="status-text" id="run-status"></div>
              </div>
            </div>
          </article>
        </section>
      </div>
    </div>

    <script>
      // Theme management
      const themeToggle = document.getElementById('theme-toggle');
      const html = document.documentElement;
      
      const savedTheme = localStorage.getItem('{LOCALSTORAGE_THEME_KEY_API}') || 'dark';
      html.setAttribute('data-theme', savedTheme);
      
      themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('{LOCALSTORAGE_THEME_KEY_API}', newTheme);
      });

      // Dashboard functionality
      const endpointListEl = document.getElementById("endpoint-list");
      const endpointCountEl = document.getElementById("endpoint-count");
      const detailMetaEl = document.getElementById("detail-meta");
      const detailSampleEl = document.getElementById("detail-sample");
      const detailMethodPillEl = document.getElementById("detail-method-pill");
      const btnRunEl = document.getElementById("btn-run");
      const runStatusEl = document.getElementById("run-status");

      let endpoints = [];
      let activeKey = null;

      function methodClass(method) {
        switch (method) {
          case "GET": return "method-pill method-get";
          case "POST": return "method-pill method-post";
          case "PUT": return "method-pill method-put";
          case "PATCH": return "method-pill method-patch";
          case "DELETE": return "method-pill method-delete";
        }
        return "method-pill";
      }

      function renderList() {
        endpointListEl.innerHTML = "";
        if (!endpoints.length) {
          endpointCountEl.textContent = "0 endpoints";
          endpointListEl.innerHTML = '<div style="font-size:0.8rem;color:var(--text-muted);">No endpoints registered yet. Import <code>register_endpoint_sample</code> in your controllers and register samples to see them here.</div>';
          return;
        }
        endpointCountEl.textContent = endpoints.length + " endpoints";

        for (const ep of endpoints) {
          const row = document.createElement("div");
          row.className = "endpoint-row" + (ep.key === activeKey ? " active" : "");
          row.dataset.key = ep.key;

          const method = document.createElement("span");
          method.className = methodClass(ep.method);
          method.textContent = ep.method;

          const main = document.createElement("div");
          main.className = "endpoint-main";
          const name = document.createElement("div");
          name.className = "endpoint-name";
          name.textContent = ep.name;
          const path = document.createElement("div");
          path.className = "endpoint-path";
          path.textContent = ep.path;
          main.appendChild(name);
          main.appendChild(path);

          const statusDot = document.createElement("div");
          statusDot.className = "status-dot";
          statusDot.id = "status-dot-" + ep.key;

          row.appendChild(method);
          row.appendChild(main);
          row.appendChild(statusDot);

          row.addEventListener("click", () => selectEndpoint(ep.key));
          endpointListEl.appendChild(row);
        }
      }

      function selectEndpoint(key) {
        activeKey = key;
        for (const row of endpointListEl.querySelectorAll(".endpoint-row")) {
          row.classList.toggle("active", row.dataset.key === key);
        }
        const ep = endpoints.find(e => e.key === key);
        if (!ep) return;

        detailMetaEl.textContent = ep.description || (ep.method + " " + ep.path);
        detailSampleEl.textContent = JSON.stringify(ep.sampleRequest || {}, null, 2);
        detailMethodPillEl.style.display = "inline-flex";
        detailMethodPillEl.textContent = ep.method + "  " + ep.path;
        btnRunEl.disabled = false;
        runStatusEl.textContent = "";
        runStatusEl.className = "status-text";
      }

      async function loadEndpoints() {
        try {
          const res = await fetch("{ROUTER_PREFIX_API}/endpoints");
          if (!res.ok) {
            throw new Error("Failed to load endpoints");
          }
          endpoints = await res.json();
          renderList();
        } catch (err) {
          console.error(err);
          endpointCountEl.textContent = "Error loading endpoints";
        }
      }

      async function runSample() {
        if (!activeKey) return;
        btnRunEl.disabled = true;
        runStatusEl.textContent = "Running…";
        runStatusEl.className = "status-text";
        try {
          const res = await fetch("{ROUTER_PREFIX_API}/test/" + encodeURIComponent(activeKey), {
            method: "POST"
          });
          const body = await res.json();
          const ok = body.ok === true;
          const label = (ok ? "OK " : "Error ") + "(" + body.status + ", " + body.latency_ms.toFixed(1) + " ms)";
          runStatusEl.textContent = label;
          runStatusEl.className = "status-text " + (ok ? "ok" : "error");
          const dot = document.getElementById("status-dot-" + activeKey);
          if (dot) {
            dot.classList.remove("ok", "error");
            dot.classList.add(ok ? "ok" : "error");
          }
        } catch (err) {
          console.error(err);
          runStatusEl.textContent = "Request failed";
          runStatusEl.className = "status-text error";
        } finally {
          btnRunEl.disabled = false;
        }
      }

      btnRunEl.addEventListener("click", runSample);
      loadEndpoints();
    </script>
  </body>
</html>
    """
    )
    return HTMLResponse(content=html)


@router.get(
    "/endpoints", response_class=JSONResponse, summary="List configured API samples"
)
async def list_endpoints() -> JSONResponse:
    """Return the list of registered endpoint samples as JSON."""
    samples = list_endpoint_samples()
    return JSONResponse(content=[_serialize_sample(s) for s in samples])


@router.post(
    "/test/{key}",
    response_class=JSONResponse,
    summary="Run sample request for an endpoint",
)
async def test_endpoint(key: str, request: Request) -> JSONResponse:
    """Execute the sample request for the given endpoint key against this API.

    This uses httpx to send a request back to the same FastAPI instance,
    so it respects middleware and routing exactly as a real client would.
    """
    sample = get_endpoint_sample(key)
    if not sample or not sample.enabled:
        raise HTTPException(status_code=404, detail="Endpoint sample not found.")

    base_url = str(request.base_url).rstrip("/")
    url = f"{base_url}{sample.path}"
    method = sample.method.upper()
    json_body = sample.sample_request or None
    params = sample.sample_query or None
    headers = sample.sample_headers or None

    import time as _time

    start = _time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_body,
                params=params,
                headers=headers,
            )
        elapsed_ms = (float(_time.perf_counter() - start)) * 1000.0
        truncated_body: Any
        try:
            data = response.json()
            serialized = json.dumps(data)
        except Exception:
            serialized = response.text or ""
        if len(serialized) > MAX_BODY_PREVIEW_LENGTH:
            truncated_body = serialized[:MAX_BODY_PREVIEW_LENGTH] + "…"  # type: ignore
        else:
            truncated_body = serialized

        return JSONResponse(
            content={
                "ok": response.status_code < HTTP_STATUS_SERVER_ERROR_THRESHOLD,
                "status": response.status_code,
                "latency_ms": elapsed_ms,
                "body": truncated_body,
            }
        )
    except Exception as exc:
        elapsed_ms = (float(_time.perf_counter() - start)) * 1000.0
        return JSONResponse(
            content={
                "ok": False,
                "status": 0,
                "latency_ms": elapsed_ms,
                "error": f"{exc}"[0:MAX_ERROR_LENGTH],  # type: ignore
            },
            status_code=HTTPStatus.OK.value,
        )
