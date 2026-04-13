"""Queues & Jobs Dashboard Router with beautiful visualizations."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from fast_dashboards.core.constants import (
    AUTO_REFRESH_INTERVAL_MS,
    DEFAULT_SITE_NAME,
    LOCALSTORAGE_THEME_KEY_QUEUES,
    RABBITMQ_TIMEOUT_SECONDS,
    ROUTER_PREFIX_QUEUES,
    STATUS_ACTIVE,
    STATUS_DISABLED,
    STATUS_ERROR,
    STATUS_IDLE,
    WORKER_BACKEND_CELERY,
    WORKER_BACKEND_DRAMATIQ,
    WORKER_BACKEND_RQ,
)
from fast_dashboards.core.registry import registry
from fast_dashboards.core.seo import render_dashboard_inline_head
from fast_dashboards.core._optional_import import optional_import

boto3, _ = optional_import("boto3")
_celery_mod, Celery = optional_import("celery", "Celery")
rq, _ = optional_import("rq")
_redis_mod, Redis = optional_import("redis", "Redis")
_rq_registry_mod, FailedJobRegistry = optional_import(
    "rq.registry", "FailedJobRegistry"
)


def _get_jobs_config() -> Optional[Any]:
    """Get jobs configuration via registry."""
    cfg_class = registry.get_config("jobs")
    if cfg_class and hasattr(cfg_class, "instance"):
        return cfg_class.instance().get_config()
    return None


def _get_queues_config() -> Optional[Any]:
    """Get queues configuration via registry."""
    cfg_class = registry.get_config("queues")
    if cfg_class and hasattr(cfg_class, "instance"):
        return cfg_class.instance().get_config()
    return None


router = APIRouter(prefix=ROUTER_PREFIX_QUEUES, tags=["Queues Dashboard"])


def _inspect_rabbitmq(cfg) -> Optional[Dict[str, Any]]:
    """Execute _inspect_rabbitmq operation.

    Args:
        cfg: The cfg parameter.

    Returns:
        The result of the operation.
    """
    if not (cfg.enabled and cfg.url):
        return None
    management_url = getattr(cfg, "management_url", None)
    if not management_url:
        return None
    try:
        auth = None
        username = getattr(cfg, "username", None)
        password = getattr(cfg, "password", None)
        if username and password:
            auth = (username, password)
        api_url = management_url.rstrip("/") + "/api/queues"
        resp = httpx.get(api_url, auth=auth, timeout=RABBITMQ_TIMEOUT_SECONDS)
        resp.raise_for_status()
        queues = resp.json()
        total_ready = 0
        total_unacked = 0
        for q in queues:
            try:
                total_ready += int(q.get("messages", 0))
                total_unacked += int(q.get("messages_unacknowledged", 0))
            except Exception:
                continue
        return {
            "backend": "rabbitmq",
            "name": management_url,
            "messages": total_ready,
            "inFlight": total_unacked,
            "delayed": 0,
            "icon": "🐰",
            "color": "#ff6b6b",
        }
    except Exception as exc:
        logger.warning(f"RabbitMQ inspection failed: {exc}")
        return {
            "backend": "rabbitmq",
            "name": management_url or cfg.url,
            "error": str(exc)[:50],
            "icon": "🐰",
            "color": "#ff6b6b",
        }


def _inspect_sqs(cfg) -> Optional[Dict[str, Any]]:
    """Execute _inspect_sqs operation.

    Args:
        cfg: The cfg parameter.

    Returns:
        The result of the operation.
    """
    if not (cfg.enabled and cfg.queue_url and boto3 is not None):
        return None
    try:
        session_kwargs: Dict[str, Any] = {}
        if cfg.access_key_id and cfg.secret_access_key:
            session_kwargs.update(
                aws_access_key_id=cfg.access_key_id,
                aws_secret_access_key=cfg.secret_access_key,
            )
        sqs = boto3.client("sqs", region_name=cfg.region, **session_kwargs)
        attrs = sqs.get_queue_attributes(
            QueueUrl=cfg.queue_url,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "ApproximateNumberOfMessagesDelayed",
            ],
        )["Attributes"]
        return {
            "backend": "sqs",
            "name": cfg.queue_url.split("/")[-1],
            "messages": int(attrs.get("ApproximateNumberOfMessages", "0")),
            "inFlight": int(attrs.get("ApproximateNumberOfMessagesNotVisible", "0")),
            "delayed": int(attrs.get("ApproximateNumberOfMessagesDelayed", "0")),
            "icon": "📦",
            "color": "#f59e0b",
        }
    except Exception as exc:
        logger.warning(f"SQS inspection failed: {exc}")
        return {
            "backend": "sqs",
            "name": cfg.queue_url.split("/")[-1] if cfg.queue_url else "SQS",
            "error": str(exc)[:50],
            "icon": "📦",
            "color": "#f59e0b",
        }


def _inspect_jobs() -> Dict[str, Any]:
    """Execute _inspect_jobs operation.

    Returns:
        The result of the operation.
    """
    cfg = _get_jobs_config()
    if cfg is None:
        return {
            WORKER_BACKEND_CELERY: {
                "enabled": False,
                "workers": 0,
                "active": 0,
                "icon": "🌿",
                "color": "#22c55e",
                "status": STATUS_DISABLED,
            },
            WORKER_BACKEND_RQ: {
                "enabled": False,
                "queueSize": 0,
                "failed": 0,
                "icon": "🔴",
                "color": "#ef4444",
                "status": STATUS_DISABLED,
            },
            WORKER_BACKEND_DRAMATIQ: {
                "enabled": False,
                "status": "n/a",
                "icon": "🎭",
                "color": "#8b5cf6",
                "status": STATUS_DISABLED,
            },
        }

    out: Dict[str, Any] = {
        WORKER_BACKEND_CELERY: {
            "enabled": cfg.celery.enabled,
            "workers": 0,
            "active": 0,
            "icon": "🌿",
            "color": "#22c55e",
            "status": STATUS_IDLE,
        },
        WORKER_BACKEND_RQ: {
            "enabled": cfg.rq.enabled,
            "queueSize": 0,
            "failed": 0,
            "icon": "🔴",
            "color": "#ef4444",
            "status": STATUS_IDLE,
        },
        WORKER_BACKEND_DRAMATIQ: {
            "enabled": cfg.dramatiq.enabled,
            "status": "configured" if cfg.dramatiq.enabled else "n/a",
            "icon": "🎭",
            "color": "#8b5cf6",
            "status": STATUS_IDLE,
        },
    }

    if cfg.celery.enabled and Celery is not None:
        try:
            app = Celery(
                cfg.celery.namespace,
                broker=cfg.celery.broker_url,
                backend=cfg.celery.result_backend,
            )
            insp = app.control.inspect()
            active = insp.active() or {}
            out[WORKER_BACKEND_CELERY]["workers"] = len(active)
            out[WORKER_BACKEND_CELERY]["active"] = sum(len(tasks or []) for tasks in active.values())
            out[WORKER_BACKEND_CELERY]["status"] = STATUS_ACTIVE if len(active) > 0 else STATUS_IDLE
        except Exception as exc:
            logger.warning(f"Celery inspection failed: {exc}")
            out[WORKER_BACKEND_CELERY]["error"] = str(exc)[:30]
            out[WORKER_BACKEND_CELERY]["status"] = STATUS_ERROR

    if (
        cfg.rq.enabled
        and rq is not None
        and Redis is not None
        and FailedJobRegistry is not None
    ):
        try:
            redis_conn = Redis.from_url(cfg.rq.redis_url)
            queue = rq.Queue(cfg.rq.queue_name, connection=redis_conn)
            out[WORKER_BACKEND_RQ]["queueSize"] = queue.count
            failed_registry = FailedJobRegistry(
                cfg.rq.queue_name, connection=redis_conn
            )
            out[WORKER_BACKEND_RQ]["failed"] = len(failed_registry)
            out[WORKER_BACKEND_RQ]["status"] = STATUS_ACTIVE if queue.count > 0 else STATUS_IDLE
        except Exception as exc:
            logger.warning(f"RQ inspection failed: {exc}")
            out[WORKER_BACKEND_RQ]["error"] = str(exc)[:30]
            out[WORKER_BACKEND_RQ]["status"] = STATUS_ERROR

    if cfg.dramatiq.enabled:
        out[WORKER_BACKEND_DRAMATIQ]["status"] = "configured"

    return out


@router.get("", response_class=HTMLResponse, summary="Queues & Jobs Dashboard")
async def queues_dashboard() -> HTMLResponse:
    """Render the queues & jobs dashboard page."""
    _head_seo = render_dashboard_inline_head(
        page_title=f"{DEFAULT_SITE_NAME} Queues & Jobs Dashboard",
        description="Queue backends, workers, and job runner status for RabbitMQ, SQS, NATS, Celery, RQ, and Dramatiq.",
        path=ROUTER_PREFIX_QUEUES,
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    {_head_seo}
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
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
        }}

        [data-theme="light"] {{
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
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            transition: all 0.3s ease;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .header {{
            margin-bottom: 2.5rem;
            position: relative;
        }}
        
        .header-content {{ 
            position: relative; 
            z-index: 1; 
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .header-title-group {{
            flex: 1;
        }}
        
        .header-title {{
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.3s ease;
        }}
        
        .header-subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }}

        /* Theme Toggle */
        .theme-toggle {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.6rem;
            cursor: pointer;
            color: var(--text);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .theme-toggle:hover {{
            border-color: var(--border-hover);
            background: var(--surface);
        }}

        .theme-toggle svg {{
            width: 20px;
            height: 20px;
        }}

        .theme-toggle .sun-icon {{ display: none; }}
        .theme-toggle .moon-icon {{ display: block; }}

        [data-theme="light"] .theme-toggle .sun-icon {{ display: block; }}
        [data-theme="light"] .theme-toggle .moon-icon {{ display: none; }}
        
        /* Grid Layout */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}
        
        @media (max-width: 1024px) {{
            .dashboard-grid {{ grid-template-columns: 1fr; }}
        }}
        
        /* Section Cards */
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}

        .section-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .section-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.3s ease;
        }}
        
        .section-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .section-icon {{
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            transition: all 0.3s ease;
        }}
        
        .live-indicator {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
        }}
        
        .live-dot {{
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }}
            50% {{ opacity: 0.8; box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
        }}
        
        .section-content {{ padding: 1.5rem; }}
        
        /* Queue Items */
        .queue-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .queue-item {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }}
        
        .queue-item:hover {{
            transform: translateX(4px);
            border-color: var(--border-hover);
        }}
        
        .queue-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .queue-icon {{
            font-size: 1.75rem;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--surface);
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .queue-info {{ flex: 1; }}
        
        .queue-name {{
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .queue-backend {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
        }}
        
        .queue-status {{
            padding: 0.375rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            transition: all 0.3s ease;
        }}
        
        .queue-status.active {{ background: rgba(34, 197, 94, 0.15); color: var(--success); }}
        .queue-status.error {{ background: rgba(239, 68, 68, 0.15); color: var(--error); }}
        .queue-status.idle {{ background: var(--surface); color: var(--text-secondary); border: 1px solid var(--border); }}
        
        /* Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.75rem;
        }}
        
        .metric-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.75rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .metric-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .metric-label {{
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            transition: all 0.3s ease;
        }}
        
        /* Worker Cards */
        .worker-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .worker-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }}

        .worker-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .worker-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .worker-icon {{
            font-size: 1.5rem;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--surface);
            border-radius: 10px;
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .worker-info {{ flex: 1; }}
        
        .worker-name {{
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .status-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        .worker-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 0.5rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            transition: all 0.3s ease;
        }}
        
        .stat-value {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .stat-label {{
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            transition: all 0.3s ease;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }}
        
        .empty-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}
        
        /* Loading Animation */
        .loading-skeleton {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            background-image: linear-gradient(90deg, var(--surface-raised) 25%, var(--surface) 50%, var(--surface-raised) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
            height: 80px;
            transition: all 0.3s ease;
        }}
        
        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="header-content">
                <div class="header-title-group">
                    <h1 class="header-title">⚡ Queues & Jobs</h1>
                    <p class="header-subtitle">Real-time monitoring of message queues and background workers</p>
                </div>
                <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
                    <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                </button>
            </div>
        </header>
        
        <div class="dashboard-grid">
            <!-- Queues Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">📬</div>
                        Message Queues
                    </div>
                    <div class="live-indicator">
                        <div class="live-dot"></div>
                        Live
                    </div>
                </div>
                <div class="section-content">
                    <div class="queue-list" id="queues-list">
                        <div class="loading-skeleton"></div>
                        <div class="loading-skeleton"></div>
                    </div>
                </div>
            </div>
            
            <!-- Workers Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">👷</div>
                        Job Workers
                    </div>
                    <div class="live-indicator">
                        <div class="live-dot"></div>
                        Live
                    </div>
                </div>
                <div class="section-content">
                    <div class="worker-list" id="workers-list">
                        <div class="loading-skeleton"></div>
                        <div class="loading-skeleton"></div>
                        <div class="loading-skeleton"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Theme management
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;
        
        const savedTheme = localStorage.getItem('{LOCALSTORAGE_THEME_KEY_QUEUES}');
        if (savedTheme) {{
            html.setAttribute('data-theme', savedTheme);
        }} else if (window.matchMedia('(prefers-color-scheme: light)').matches) {{
            html.setAttribute('data-theme', 'light');
        }}
        
        themeToggle.addEventListener('click', () => {{
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('{LOCALSTORAGE_THEME_KEY_QUEUES}', newTheme);
        }});
        
        async function loadState() {{
            try {{
                const res = await fetch(window.location.pathname + '/state');
                const data = await res.json();
                renderQueues(data.queues || []);
                renderWorkers(data.jobs || {{}});
            }} catch (e) {{
                console.error('Failed to load state:', e);
            }}
        }}
        
        function renderQueues(queues) {{
            const container = document.getElementById('queues-list');
            if (!queues.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📭</div>
                        <p>No queues configured</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = queues.map(q => {{
                const hasError = q.error;
                const statusClass = hasError ? 'error' : q.messages > 0 ? 'active' : 'idle';
                const statusText = hasError ? 'Error' : q.messages > 0 ? 'Active' : 'Idle';
                
                return `
                    <div class="queue-item">
                        <div class="queue-header">
                            <div class="queue-icon">${{q.icon || '📦'}}</div>
                            <div class="queue-info">
                                <div class="queue-name">${{q.name}}</div>
                                <div class="queue-backend">${{q.backend}}</div>
                            </div>
                            <span class="queue-status ${{statusClass}}">${{statusText}}</span>
                        </div>
                        ${{hasError ? `<p style="color: var(--error); font-size: 0.875rem;">${{q.error}}</p>` : `
                        <div class="metrics-grid">
                            <div class="metric-box">
                                <div class="metric-value">${{q.messages || 0}}</div>
                                <div class="metric-label">Messages</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-value">${{q.inFlight || 0}}</div>
                                <div class="metric-label">In Flight</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-value">${{q.delayed || 0}}</div>
                                <div class="metric-label">Delayed</div>
                            </div>
                        </div>
                        `}}
                    </div>
                `;
            }}).join('');
        }}
        
        function renderWorkers(jobs) {{
            const container = document.getElementById('workers-list');
            const workers = Object.entries(jobs);
            
            if (!workers.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">😴</div>
                        <p>No workers configured</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = workers.map(([name, info]) => {{
                const statusColor = info.status === 'active' ? 'var(--success)' : info.status === 'error' ? 'var(--error)' : 'var(--text-muted)';
                
                let statsHtml = '';
                if (name === '{WORKER_BACKEND_CELERY}') {{
                    statsHtml = `
                        <div class="stat-item"><div class="stat-value">${{info.workers || 0}}</div><div class="stat-label">Workers</div></div>
                        <div class="stat-item"><div class="stat-value">${{info.active || 0}}</div><div class="stat-label">Active</div></div>
                        <div class="stat-item"><div class="stat-value">${{info.enabled ? 'On' : 'Off'}}</div><div class="stat-label">Status</div></div>
                    `;
                }} else if (name === '{WORKER_BACKEND_RQ}') {{
                    statsHtml = `
                        <div class="stat-item"><div class="stat-value">${{info.queueSize || 0}}</div><div class="stat-label">Queue</div></div>
                        <div class="stat-item"><div class="stat-value">${{info.failed || 0}}</div><div class="stat-label">Failed</div></div>
                        <div class="stat-item"><div class="stat-value">${{info.enabled ? 'On' : 'Off'}}</div><div class="stat-label">Status</div></div>
                    `;
                }} else {{
                    statsHtml = `
                        <div class="stat-item"><div class="stat-value">-</div><div class="stat-label">Queue</div></div>
                        <div class="stat-item"><div class="stat-value">-</div><div class="stat-label">Failed</div></div>
                        <div class="stat-item"><div class="stat-value">${{info.enabled ? 'On' : 'Off'}}</div><div class="stat-label">Status</div></div>
                    `;
                }}
                
                return `
                    <div class="worker-card">
                        <div class="worker-header">
                            <div class="worker-icon">${{info.icon || '⚙️'}}</div>
                            <div class="worker-info">
                                <div class="worker-name">
                                    <span class="status-indicator" style="background: ${{statusColor}};"></span>
                                    ${{name.charAt(0).toUpperCase() + name.slice(1)}}
                                </div>
                            </div>
                        </div>
                        <div class="worker-stats">${{statsHtml}}</div>
                    </div>
                `;
            }}).join('');
        }}
        
        loadState();
        setInterval(loadState, {AUTO_REFRESH_INTERVAL_MS});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/state", response_class=JSONResponse, summary="Queues & jobs state")
async def queues_state() -> JSONResponse:
    """Return JSON snapshot of queues and worker state."""
    q_cfg = _get_queues_config()
    queues: List[Dict[str, Any]] = []

    if q_cfg is not None:
        rabbit_info = _inspect_rabbitmq(q_cfg.rabbitmq)
        if rabbit_info is not None:
            queues.append(rabbit_info)
        sqs_info = _inspect_sqs(q_cfg.sqs)
        if sqs_info is not None:
            queues.append(sqs_info)

    jobs = _inspect_jobs()
    return JSONResponse({"queues": queues, "jobs": jobs})


__all__ = ["router"]
