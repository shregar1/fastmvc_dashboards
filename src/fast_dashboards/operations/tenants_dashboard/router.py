"""Tenants, Auth & Feature Flags Dashboard Router with beautiful UI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from fast_dashboards.core.constants import (
    AUTO_REFRESH_INTERVAL_MS,
    DEFAULT_SITE_NAME,
    LOCALSTORAGE_THEME_KEY_TENANTS,
    ROUTER_PREFIX_TENANTS,
)
from fast_dashboards.core.registry import registry
from fast_dashboards.core.seo import render_dashboard_inline_head

router = APIRouter(prefix=ROUTER_PREFIX_TENANTS, tags=["Tenants Dashboard"])


async def _load_tenants() -> List[Dict[str, Any]]:
    """Load tenants from the registered tenant store."""
    store = registry.get_tenant_store()
    if store is None:
        return []

    try:
        tenants = await store.list_all(active_only=False)
        return [t.to_dict() if hasattr(t, "to_dict") else dict(t) for t in tenants]
    except Exception:
        try:
            tenants = store.list_all()
            return [t.to_dict() if hasattr(t, "to_dict") else dict(t) for t in tenants]
        except Exception:
            return []


def _load_feature_flags() -> Dict[str, Any]:
    """Load feature flags configuration via registry."""
    cfg_class = registry.get_config("feature_flags")
    if cfg_class is None or not hasattr(cfg_class, "instance"):
        return {
            "launchdarkly": {"enabled": False, "mode": "Not configured"},
            "unleash": {"enabled": False, "mode": "Not configured"},
        }

    try:
        cfg = cfg_class.instance().get_config()
        return {
            "launchdarkly": {
                "enabled": getattr(cfg.launchdarkly, "enabled", False),
                "mode": "SDK Active"
                if getattr(cfg.launchdarkly, "sdk_key", None)
                else "SDK Key Missing",
                "userKey": getattr(cfg.launchdarkly, "default_user_key", ""),
                "icon": "🚀",
                "color": "#3b82f6",
            },
            "unleash": {
                "enabled": getattr(cfg.unleash, "enabled", False),
                "mode": "Connected"
                if getattr(cfg.unleash, "api_key", None)
                else "API Key Missing",
                "url": getattr(cfg.unleash, "url", ""),
                "appName": getattr(cfg.unleash, "app_name", ""),
                "icon": "🐆",
                "color": "#8b5cf6",
            },
        }
    except Exception as e:
        return {
            "launchdarkly": {
                "enabled": False,
                "mode": f"Error: {str(e)[:30]}",
                "icon": "🚀",
                "color": "#3b82f6",
            },
            "unleash": {
                "enabled": False,
                "mode": "Error",
                "icon": "🐆",
                "color": "#8b5cf6",
            },
        }


def _load_identity_providers() -> Dict[str, Any]:
    """Load identity providers configuration via registry."""
    cfg_class = registry.get_config("identity")
    if cfg_class is None or not hasattr(cfg_class, "instance"):
        return {}

    try:
        cfg = cfg_class.instance().get_config()
        providers = {}

        idp_configs = {
            "google": ("Google", "🔵", "#ea4335"),
            "github": ("GitHub", "⚫", "#333"),
            "azure_ad": ("Azure AD", "🔷", "#0078d4"),
            "okta": ("Okta", "🟣", "#007dc1"),
            "auth0": ("Auth0", "🟠", "#eb5424"),
            "saml": ("SAML", "🛡️", "#10b981"),
        }

        for key, (name, icon, color) in idp_configs.items():
            provider = getattr(cfg, key, None)
            if provider:
                is_configured = bool(
                    getattr(provider, "client_id", None)
                    or getattr(provider, "idp_metadata_url", None)
                )
                providers[key] = {
                    "name": name,
                    "enabled": getattr(provider, "enabled", False),
                    "configured": is_configured,
                    "redirectUri": getattr(
                        provider, "redirect_uri", getattr(provider, "acs_url", "")
                    ),
                    "icon": icon,
                    "color": color,
                }

        return providers
    except Exception:
        return {}


def _load_quotas() -> Dict[str, Any]:
    """Load rate limit configuration via registry."""
    cfg_class = registry.get_config("rate_limit")
    if cfg_class is None or not hasattr(cfg_class, "instance"):
        return {"enabled": False, "mode": "Not configured"}

    try:
        cfg = cfg_class.instance().get_config()
        return {
            "enabled": getattr(cfg, "enabled", False),
            "defaultPerMinute": getattr(cfg, "default_per_minute", 60),
            "defaultBurst": getattr(cfg, "default_burst", 10),
            "overrides": len(getattr(cfg, "per_tenant_overrides", {})),
        }
    except Exception as e:
        return {"enabled": False, "mode": f"Error: {str(e)[:30]}"}


@router.get("", response_class=HTMLResponse, summary="Tenants & Auth Dashboard")
async def tenants_dashboard() -> HTMLResponse:
    """Render the tenants/auth/feature-flags dashboard page."""
    _head_seo = render_dashboard_inline_head(
        page_title=f"{DEFAULT_SITE_NAME} Tenants & Auth Dashboard",
        description="Tenants, identity providers, feature flags, and rate-limit configuration overview.",
        path=ROUTER_PREFIX_TENANTS,
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
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; transition: all 0.3s ease; }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
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
        }}
        
        .header-subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        
        /* Theme Toggle */
        .theme-toggle {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 0.75rem;
            cursor: pointer;
            color: var(--text);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            border-color: var(--border-hover);
            background: var(--surface-raised);
        }}
        
        .theme-toggle svg {{
            width: 20px;
            height: 20px;
        }}
        
        [data-theme="light"] .theme-toggle .moon-icon {{ display: none; }}
        [data-theme="dark"] .theme-toggle .sun-icon {{ display: none; }}
        
        /* Grid Layout */
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
        }}
        
        @media (max-width: 1200px) {{
            .dashboard-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{ grid-template-columns: 1fr; }}
            .header-content {{ flex-direction: column; gap: 1rem; }}
        }}
        
        /* Section Cards */
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        
        .section-card.large {{
            grid-column: span 2;
        }}
        
        @media (max-width: 1200px) {{
            .section-card.large {{ grid-column: span 1; }}
        }}
        
        .section-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .section-title {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.1rem;
            font-weight: 600;
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
        }}
        
        .badge {{
            padding: 0.375rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            background: var(--surface-raised);
            color: var(--text-secondary);
            border: 1px solid var(--border);
        }}
        
        .section-content {{
            padding: 1.5rem;
            flex: 1;
        }}
        
        /* Tenant Cards */
        .tenant-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .tenant-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            cursor: pointer;
        }}
        
        .tenant-card:hover {{
            border-color: var(--border-hover);
            background: var(--surface);
        }}
        
        .tenant-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        
        .tenant-avatar {{
            width: 48px;
            height: 48px;
            border-radius: 12px;
            background: var(--surface);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text);
        }}
        
        .tenant-info {{ flex: 1; }}
        
        .tenant-name {{
            font-weight: 600;
            font-size: 1rem;
            margin-bottom: 0.25rem;
            color: var(--text);
        }}
        
        .tenant-slug {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: 'Monaco', monospace;
        }}
        
        .tenant-status {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
        }}
        
        .tenant-status.inactive {{ background: var(--text-muted); }}
        
        .tenant-features {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .feature-tag {{
            padding: 0.25rem 0.625rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }}
        
        /* Provider Cards */
        .provider-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }}
        
        .provider-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
        }}
        
        .provider-card:hover {{
            border-color: var(--border-hover);
            background: var(--surface);
        }}
        
        .provider-header {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }}
        
        .provider-icon {{
            font-size: 1.5rem;
        }}
        
        .provider-name {{
            font-weight: 600;
            flex: 1;
            color: var(--text);
        }}
        
        .provider-status {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        
        .provider-status.enabled {{ background: var(--success); }}
        .provider-status.disabled {{ background: var(--text-muted); }}
        
        .provider-config {{
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}
        
        /* Feature Flag Cards */
        .ff-list {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}
        
        .ff-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.25rem;
        }}
        
        .ff-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .ff-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        
        .ff-icon {{
            font-size: 1.75rem;
        }}
        
        .ff-info {{ flex: 1; }}
        
        .ff-name {{
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--text);
        }}
        
        .ff-mode {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}
        
        .ff-toggle {{
            width: 48px;
            height: 26px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 13px;
            position: relative;
        }}
        
        .ff-toggle.active {{ background: var(--success); border-color: var(--success); }}
        
        .ff-toggle::after {{
            content: '';
            position: absolute;
            top: 3px;
            left: 3px;
            width: 18px;
            height: 18px;
            background: var(--text);
            border-radius: 50%;
        }}
        
        .ff-toggle.active::after {{
            left: auto;
            right: 3px;
        }}
        
        /* Rate Limit Card */
        .rl-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        
        .rl-stat {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }}
        
        .rl-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
        }}
        
        .rl-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .rl-visual {{
            height: 8px;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 1rem;
        }}
        
        .rl-bar {{
            height: 100%;
            background: var(--accent);
            border-radius: 2px;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-muted);
        }}
        
        .empty-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}
        
        /* Loading */
        .skeleton {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 8px;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="header-content">
                <div class="header-title-group">
                    <h1 class="header-title">🏢 Tenants & Auth</h1>
                    <p class="header-subtitle">Multi-tenant configuration, identity providers, and feature flags</p>
                </div>
                <button class="theme-toggle" id="themeToggle" aria-label="Toggle theme">
                    <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/>
                        <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
                    </svg>
                    <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                    </svg>
                </button>
            </div>
        </header>
        
        <div class="dashboard-grid">
            <!-- Tenants Section -->
            <div class="section-card large">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">🏢</div>
                        Tenants
                    </div>
                    <span class="badge" id="tenant-count">Loading...</span>
                </div>
                <div class="section-content">
                    <div class="tenant-list" id="tenant-list">
                        <div class="skeleton" style="height: 80px; margin-bottom: 1rem;"></div>
                        <div class="skeleton" style="height: 80px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Identity Providers Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">🔐</div>
                        Identity Providers
                    </div>
                </div>
                <div class="section-content">
                    <div class="provider-grid" id="provider-list">
                        <div class="skeleton" style="height: 60px;"></div>
                        <div class="skeleton" style="height: 60px;"></div>
                        <div class="skeleton" style="height: 60px;"></div>
                        <div class="skeleton" style="height: 60px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Feature Flags Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">🚩</div>
                        Feature Flags
                    </div>
                </div>
                <div class="section-content">
                    <div class="ff-list" id="ff-list">
                        <div class="skeleton" style="height: 80px; margin-bottom: 1rem;"></div>
                        <div class="skeleton" style="height: 80px;"></div>
                    </div>
                </div>
            </div>
            
            <!-- Rate Limits Section -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">⏱️</div>
                        Rate Limits
                    </div>
                    <span class="badge" id="rl-status">Loading...</span>
                </div>
                <div class="section-content">
                    <div id="rl-content">
                        <div class="skeleton" style="height: 120px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Theme management
        const themeToggle = document.getElementById('themeToggle');
        const html = document.documentElement;
        
        function getStoredTheme() {{
            try {{ return localStorage.getItem('{LOCALSTORAGE_THEME_KEY_TENANTS}'); }} catch (e) {{ return null; }}
        }}
        
        function setStoredTheme(theme) {{
            try {{ localStorage.setItem('{LOCALSTORAGE_THEME_KEY_TENANTS}', theme); }} catch (e) {{}}
        }}
        
        function applyTheme(theme) {{
            if (theme === 'light') {{
                html.setAttribute('data-theme', 'light');
            }} else {{
                html.setAttribute('data-theme', 'dark');
            }}
        }}
        
        themeToggle.addEventListener('click', () => {{
            const current = html.getAttribute('data-theme');
            const next = current === 'light' ? 'dark' : 'light';
            applyTheme(next);
            setStoredTheme(next);
        }});
        
        // Initialize theme
        const savedTheme = getStoredTheme();
        if (savedTheme) {{
            applyTheme(savedTheme);
        }} else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {{
            applyTheme('light');
        }}
        
        async function loadState() {{
            try {{
                const res = await fetch(window.location.pathname + '/state');
                const data = await res.json();
                renderTenants(data.tenants || []);
                renderProviders(data.idps || {{}});
                renderFeatureFlags(data.flags || {{}});
                renderRateLimits(data.quotas || {{}});
            }} catch (e) {{
                console.error('Failed to load state:', e);
            }}
        }}
        
        function renderTenants(tenants) {{
            document.getElementById('tenant-count').textContent = `${{tenants.length}} tenants`;
            const container = document.getElementById('tenant-list');
            
            if (!tenants.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🏢</div>
                        <p>No tenants configured</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = tenants.map(t => `
                <div class="tenant-card">
                    <div class="tenant-header">
                        <div class="tenant-avatar">${{t.name?.[0] || 'T'}}</div>
                        <div class="tenant-info">
                            <div class="tenant-name">${{t.name || 'Unknown'}}</div>
                            <div class="tenant-slug">@${{t.slug || t.id}}</div>
                        </div>
                        <div class="tenant-status ${{t.is_active ? '' : 'inactive'}}"></div>
                    </div>
                    <div class="tenant-features">
                        ${{t.config?.features?.map(f => `<span class="feature-tag">${{f}}</span>`).join('') || '<span class="feature-tag">No features</span>'}}
                    </div>
                </div>
            `).join('');
        }}
        
        function renderProviders(providers) {{
            const container = document.getElementById('provider-list');
            const entries = Object.entries(providers);
            
            if (!entries.length) {{
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: span 2;">
                        <div class="empty-icon">🔐</div>
                        <p>No providers configured</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = entries.map(([key, p]) => `
                <div class="provider-card">
                    <div class="provider-header">
                        <span class="provider-icon">${{p.icon}}</span>
                        <span class="provider-name">${{p.name}}</span>
                        <div class="provider-status ${{p.enabled ? 'enabled' : 'disabled'}}"></div>
                    </div>
                    <div class="provider-config">
                        ${{p.configured ? '✓ Configured' : '⚠ Not configured'}}
                    </div>
                </div>
            `).join('');
        }}
        
        function renderFeatureFlags(flags) {{
            const container = document.getElementById('ff-list');
            const entries = Object.entries(flags);
            
            container.innerHTML = entries.map(([key, f]) => `
                <div class="ff-card">
                    <div class="ff-header">
                        <span class="ff-icon">${{f.icon}}</span>
                        <div class="ff-info">
                            <div class="ff-name">${{key.charAt(0).toUpperCase() + key.slice(1)}}</div>
                            <div class="ff-mode">${{f.mode}}</div>
                        </div>
                        <div class="ff-toggle ${{f.enabled ? 'active' : ''}}"></div>
                    </div>
                </div>
            `).join('');
        }}
        
        function renderRateLimits(quotas) {{
            const container = document.getElementById('rl-content');
            document.getElementById('rl-status').textContent = quotas.enabled ? 'Enabled' : 'Disabled';
            
            if (!quotas.enabled) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">⏱️</div>
                        <p>Rate limiting not enabled</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = `
                <div class="rl-stats">
                    <div class="rl-stat">
                        <div class="rl-value">${{quotas.defaultPerMinute}}</div>
                        <div class="rl-label">Requests/min</div>
                    </div>
                    <div class="rl-stat">
                        <div class="rl-value">${{quotas.defaultBurst}}</div>
                        <div class="rl-label">Burst</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.5rem;">
                    <span>Custom overrides</span>
                    <span>${{quotas.overrides}} tenants</span>
                </div>
                <div class="rl-visual">
                    <div class="rl-bar" style="width: ${{Math.min((quotas.overrides / 10) * 100, 100)}}%;"></div>
                </div>
            `;
        }}
        
        loadState();
        setInterval(loadState, {AUTO_REFRESH_INTERVAL_MS});
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/state", response_class=JSONResponse, summary="Tenants/auth state")
async def tenants_state() -> JSONResponse:
    """Execute tenants_state operation.

    Returns:
        The result of the operation.
    """
    tenants = await _load_tenants()
    flags = _load_feature_flags()
    idps = _load_identity_providers()
    quotas = _load_quotas()
    return JSONResponse(
        {"tenants": tenants, "flags": flags, "idps": idps, "quotas": quotas}
    )


__all__ = ["router"]
