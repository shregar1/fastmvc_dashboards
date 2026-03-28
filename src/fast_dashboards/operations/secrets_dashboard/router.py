"""Secrets & Configuration Dashboard Router with beautiful UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from fast_dashboards.core.registry import registry
from fast_dashboards.sec.secrets import build_secrets_backend

router = APIRouter(prefix="/dashboard/secrets", tags=["Secrets Dashboard"])


def _get_secrets_config() -> Optional[Any]:
    """Get secrets configuration via registry."""
    cfg_class = registry.get_config("secrets")
    if cfg_class and hasattr(cfg_class, "instance"):
        return cfg_class.instance().get_config()
    return None


def _load_backends_state() -> Dict[str, Any]:
    """Load secrets backends state with visual info."""
    cfg = _get_secrets_config()

    backends = {
        "vault": {
            "name": "HashiCorp Vault",
            "icon": "🔐",
            "color": "#ffd700",
            "enabled": False,
            "status": "Not configured",
        },
        "aws": {
            "name": "AWS Secrets Manager",
            "icon": "☁️",
            "color": "#ff9900",
            "enabled": False,
            "status": "Not configured",
        },
        "gcp": {
            "name": "GCP Secret Manager",
            "icon": "🔷",
            "color": "#4285f4",
            "enabled": False,
            "status": "Not configured",
        },
        "azure": {
            "name": "Azure Key Vault",
            "icon": "🔹",
            "color": "#0078d4",
            "enabled": False,
            "status": "Not configured",
        },
    }

    if cfg is None:
        return backends

    vault = getattr(cfg, "vault", None)
    if vault and getattr(vault, "enabled", False):
        backends["vault"].update(
            {
                "enabled": True,
                "url": getattr(vault, "url", ""),
                "mountPoint": getattr(vault, "mount_point", ""),
                "status": "Connected" if getattr(vault, "url", None) else "URL missing",
            }
        )

    aws = getattr(cfg, "aws", None)
    if aws and getattr(aws, "enabled", False):
        backends["aws"].update(
            {
                "enabled": True,
                "region": getattr(aws, "region", ""),
                "prefix": getattr(aws, "prefix", ""),
                "status": f"Region: {getattr(aws, 'region', 'N/A')}",
            }
        )

    gcp = getattr(cfg, "gcp", None)
    if gcp and getattr(gcp, "enabled", False):
        backends["gcp"].update(
            {
                "enabled": True,
                "projectId": getattr(gcp, "project_id", ""),
                "status": f"Project: {getattr(gcp, 'project_id', 'N/A')}"[:30],
            }
        )

    azure = getattr(cfg, "azure", None)
    if azure and getattr(azure, "enabled", False):
        backends["azure"].update(
            {
                "enabled": True,
                "vaultUrl": getattr(azure, "vault_url", ""),
                "status": "Connected"
                if getattr(azure, "vault_url", None)
                else "URL missing",
            }
        )

    return backends


async def _check_secret_health() -> Dict[str, Any]:
    """Check secrets backend health."""
    backend = build_secrets_backend()
    if backend is None:
        return {
            "hasBackend": False,
            "ok": False,
            "status": "No backend configured",
            "icon": "⚠️",
            "color": "#f59e0b",
        }

    test_name = os.getenv("SECRETS_HEALTH_CHECK_NAME", "fastmvc/health")
    try:
        value = await backend.get_secret(test_name)
        return {
            "hasBackend": True,
            "ok": value is not None,
            "status": "Secret retrieved" if value is not None else "Secret not found",
            "icon": "✅" if value is not None else "⚠️",
            "color": "#10b981" if value is not None else "#f59e0b",
        }
    except Exception as exc:
        return {
            "hasBackend": True,
            "ok": False,
            "status": str(exc)[:50],
            "icon": "❌",
            "color": "#ef4444",
        }


def _parse_env_file(path: Path) -> Dict[str, str]:
    """Parse environment file."""
    if not path.exists():
        return {}
    data: Dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _diff_envs(base: Dict[str, str], current: Dict[str, str]) -> Dict[str, Any]:
    """Compare environment files."""
    added = {k: current[k] for k in current.keys() - base.keys()}
    removed = {k: base[k] for k in base.keys() - current.keys()}
    changed = {
        k: {"from": "***", "to": "***"}
        for k in base.keys() & current.keys()
        if base[k] != current[k]
    }
    return {
        "added": len(added),
        "removed": len(removed),
        "changed": len(changed),
        "total_vars": len(current),
    }


def _load_env_diff() -> Dict[str, Any]:
    """Load environment diff."""
    root = Path(".")
    example = _parse_env_file(root / ".env.example")
    current = _parse_env_file(root / ".env")
    if not example and not current:
        return {
            "hasEnv": False,
            "diff": {"added": 0, "removed": 0, "changed": 0, "total_vars": 0},
        }
    return {"hasEnv": True, "diff": _diff_envs(example, current)}


@router.get("", response_class=HTMLResponse, summary="Secrets & Config Dashboard")
async def secrets_dashboard() -> HTMLResponse:
    """Render the secrets & configuration dashboard."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secrets & Configuration | FastMVC Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
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
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            transition: all 0.3s ease;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .header {
            margin-bottom: 2.5rem;
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        
        .header-content { position: relative; z-index: 1; }
        
        .header-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .header-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .theme-toggle {
            background: var(--surface-raised);
            border: 1px solid var(--border);
            color: var(--text);
            width: 40px;
            height: 40px;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        
        .theme-toggle:hover {
            background: var(--border);
            border-color: var(--border-hover);
        }
        
        .theme-toggle svg { width: 18px; height: 18px; }
        .theme-toggle .sun { display: none; }
        .theme-toggle .moon { display: block; }
        [data-theme="light"] .theme-toggle .sun { display: block; }
        [data-theme="light"] .theme-toggle .moon { display: none; }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.5rem;
        }
        
        @media (max-width: 1024px) {
            .dashboard-grid { grid-template-columns: 1fr; }
        }
        
        .section-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .section-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .section-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .section-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }
        
        .section-content { padding: 1.5rem; }
        
        /* Backend Grid */
        .backend-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        
        .backend-card {
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .backend-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--text-muted);
            transition: all 0.3s ease;
        }
        
        .backend-card.enabled::before { background: var(--success); }
        .backend-card:hover {
            transform: translateY(-4px);
            border-color: var(--border-hover);
        }
        
        .backend-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .backend-icon {
            font-size: 2rem;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--surface);
            border-radius: 12px;
            border: 1px solid var(--border);
        }
        
        .backend-info { flex: 1; }
        
        .backend-name {
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
            color: var(--text);
        }
        
        .backend-type {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .backend-status {
            padding: 0.375rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .backend-status.enabled {
            background: rgba(34, 197, 94, 0.15);
            color: var(--success);
        }
        
        .backend-status.disabled {
            background: rgba(113, 113, 122, 0.15);
            color: var(--text-muted);
        }
        
        .backend-meta {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-family: 'Monaco', monospace;
        }
        
        /* Health Card */
        .health-card {
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        }
        
        .health-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        
        .health-status {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text);
        }
        
        .health-message {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        /* Env Card */
        .env-card {
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
        }
        
        .env-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        
        .env-icon {
            font-size: 1.5rem;
        }
        
        .env-title {
            font-weight: 600;
            color: var(--text);
        }
        
        .env-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        
        .env-stat {
            text-align: center;
            padding: 1rem;
            background: var(--surface);
            border-radius: 12px;
        }
        
        .env-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }
        
        .env-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }
        
        .env-bar {
            height: 6px;
            background: var(--surface);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .env-progress {
            height: 100%;
            background: var(--accent);
            border-radius: 3px;
            transition: width 0.5s ease;
        }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }
        
        .empty-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }
        
        /* Skeleton */
        .skeleton {
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 8px;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="header-content">
                <h1 class="header-title">🔐 Secrets & Config</h1>
                <p class="header-subtitle">Manage secrets backends and environment configuration</p>
            </div>
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
        </header>
        
        <div class="dashboard-grid">
            <!-- Backends Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">🔐</div>
                        Secrets Backends
                    </div>
                </div>
                <div class="section-content">
                    <div class="backend-grid" id="backends-list">
                        <div class="skeleton" style="height: 120px;"></div>
                        <div class="skeleton" style="height: 120px;"></div>
                        <div class="skeleton" style="height: 120px;"></div>
                        <div class="skeleton" style="height: 120px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Sidebar -->
            <div class="sidebar">
                <!-- Health Check -->
                <div class="section-card" style="margin-bottom: 1.5rem;">
                    <div class="section-header">
                        <div class="section-title">
                            <div class="section-icon">🏥</div>
                            Health Check
                        </div>
                    </div>
                    <div class="section-content">
                        <div id="health-content">
                            <div class="skeleton" style="height: 150px;"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Environment -->
                <div class="section-card">
                    <div class="section-header">
                        <div class="section-title">
                            <div class="section-icon">📁</div>
                            Environment
                        </div>
                    </div>
                    <div class="section-content">
                        <div id="env-content">
                            <div class="skeleton" style="height: 180px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Theme management
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;
        
        const savedTheme = localStorage.getItem('theme') || 'dark';
        html.setAttribute('data-theme', savedTheme);
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
        
        async function loadState() {
            try {
                const res = await fetch(window.location.pathname + '/state');
                const data = await res.json();
                renderBackends(data.backends || {});
                renderHealth(data.health || {});
                renderEnv(data.envDiff || {});
            } catch (e) {
                console.error('Failed to load state:', e);
            }
        }
        
        function renderBackends(backends) {
            const container = document.getElementById('backends-list');
            const entries = Object.entries(backends);
            
            if (!entries.length) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: span 2;">
                        <div class="empty-icon">🔐</div>
                        <p>No backends configured</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = entries.map(([key, b]) => `
                <div class="backend-card ${b.enabled ? 'enabled' : ''}">
                    <div class="backend-header">
                        <div class="backend-icon">${b.icon}</div>
                        <div class="backend-info">
                            <div class="backend-name">${b.name}</div>
                            <div class="backend-type">${key}</div>
                        </div>
                        <span class="backend-status ${b.enabled ? 'enabled' : 'disabled'}">
                            ${b.enabled ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <div class="backend-meta">${b.status || (b.enabled ? 'Connected' : 'Not configured')}</div>
                </div>
            `).join('');
        }
        
        function renderHealth(health) {
            const container = document.getElementById('health-content');
            container.innerHTML = `
                <div class="health-card">
                    <div class="health-icon">${health.icon || '⚠️'}</div>
                    <div class="health-status" style="color: ${health.color || 'var(--text-muted)'}">
                        ${health.hasBackend ? (health.ok ? 'Healthy' : 'Issue Detected') : 'No Backend'}
                    </div>
                    <div class="health-message">${health.status || 'Configure a secrets backend'}</div>
                </div>
            `;
        }
        
        function renderEnv(env) {
            const container = document.getElementById('env-content');
            
            if (!env.hasEnv) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📁</div>
                        <p>No .env files found</p>
                    </div>
                `;
                return;
            }
            
            const diff = env.diff || {};
            const totalChanges = diff.added + diff.removed + diff.changed;
            
            container.innerHTML = `
                <div class="env-card">
                    <div class="env-header">
                        <span class="env-icon">⚡</span>
                        <span class="env-title">Environment Variables</span>
                    </div>
                    <div class="env-stats">
                        <div class="env-stat">
                            <div class="env-value">${diff.total_vars}</div>
                            <div class="env-label">Total</div>
                        </div>
                        <div class="env-stat">
                            <div class="env-value" style="color: ${totalChanges > 0 ? 'var(--warning)' : 'var(--success)'}">${totalChanges}</div>
                            <div class="env-label">Changes</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                        <span>Diff from example</span>
                    </div>
                    <div class="env-bar">
                        <div class="env-progress" style="width: ${Math.min((totalChanges / (diff.total_vars || 1)) * 100, 100)}%;"></div>
                    </div>
                </div>
            `;
        }
        
        loadState();
        setInterval(loadState, 10000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/state", response_class=JSONResponse, summary="Secrets/config state")
async def secrets_state() -> JSONResponse:
    """Execute secrets_state operation.

    Returns:
        The result of the operation.
    """
    backends = _load_backends_state()
    health = await _check_secret_health()
    env_diff = _load_env_diff()
    return JSONResponse({"backends": backends, "health": health, "envDiff": env_diff})


__all__ = ["router"]
