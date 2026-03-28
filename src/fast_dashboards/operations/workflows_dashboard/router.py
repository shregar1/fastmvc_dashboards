"""Workflows Dashboard Router with beautiful UI."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from fast_dashboards.core.registry import registry
from fast_dashboards.core.seo import render_dashboard_inline_head

router = APIRouter(prefix="/dashboard/workflows", tags=["Workflows Dashboard"])


def _get_workflows_config() -> Optional[Any]:
    """Get workflows configuration via registry."""
    cfg_class = registry.get_config("workflows")
    if cfg_class and hasattr(cfg_class, "instance"):
        return cfg_class.instance().get_config()
    return None


@router.get("", response_class=HTMLResponse, summary="Workflows Dashboard")
async def workflows_dashboard() -> HTMLResponse:
    """Render the workflows dashboard page."""
    _head_seo = render_dashboard_inline_head(
        page_title="FastMVC Workflows Dashboard",
        description="Workflow engine status, configuration, and example order lifecycle for FastMVC.",
        path="/dashboard/workflows",
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
            --info: #3b82f6;
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
            --info: #2563eb;
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
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
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
        
        .theme-toggle {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            border-color: var(--border-hover);
            background: var(--surface-raised);
        }}
        
        .theme-toggle svg {{
            width: 20px;
            height: 20px;
            fill: var(--text-secondary);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover svg {{
            fill: var(--text);
        }}
        
        .sun-icon {{ display: none; }}
        .moon-icon {{ display: block; }}
        
        [data-theme="light"] .sun-icon {{ display: block; }}
        [data-theme="light"] .moon-icon {{ display: none; }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}
        
        @media (max-width: 900px) {{
            .dashboard-grid {{ grid-template-columns: 1fr; }}
        }}
        
        .section-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .section-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .section-card.wide {{
            grid-column: span 2;
        }}
        
        @media (max-width: 900px) {{
            .section-card.wide {{ grid-column: span 1; }}
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
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .section-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            transition: all 0.3s ease;
        }}
        
        .badge {{
            padding: 0.375rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            background: var(--surface-raised);
            color: var(--text-secondary);
            border: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .section-content {{ padding: 1.5rem; }}
        
        /* Engine Card */
        .engine-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .engine-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .engine-icon {{
            font-size: 4rem;
            margin-bottom: 1rem;
        }}
        
        .engine-name {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .engine-status {{
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1.5rem;
        }}
        
        .engine-status.enabled {{
            background: rgba(34, 197, 94, 0.15);
            color: var(--success);
        }}
        
        .engine-status.disabled {{
            background: rgba(161, 161, 170, 0.15);
            color: var(--text-muted);
        }}
        
        .engine-config {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            text-align: left;
            transition: all 0.3s ease;
        }}
        
        .config-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.5rem 0;
            border-bottom: 1px solid var(--border);
            transition: all 0.3s ease;
        }}
        
        .config-row:last-child {{
            border-bottom: none;
        }}
        
        .config-label {{
            color: var(--text-muted);
            font-size: 0.875rem;
            transition: all 0.3s ease;
        }}
        
        .config-value {{
            font-family: 'Monaco', monospace;
            font-size: 0.875rem;
            color: var(--accent);
            transition: all 0.3s ease;
        }}
        
        /* Engine Options */
        .engine-options {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }}
        
        .engine-option {{
            background: var(--surface-raised);
            border: 2px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.3s ease;
            opacity: 0.5;
        }}
        
        .engine-option:hover {{
            opacity: 0.8;
            border-color: var(--border-hover);
        }}
        
        .engine-option.active {{
            border-color: var(--accent);
            opacity: 1;
        }}
        
        .engine-option-icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .engine-option-name {{
            font-weight: 600;
            font-size: 0.875rem;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }}
        
        .stat-card {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1.25rem;
            text-align: center;
            transition: all 0.3s ease;
        }}
        
        .stat-card:hover {{
            border-color: var(--border-hover);
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 0.25rem;
            transition: all 0.3s ease;
        }}
        
        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            transition: all 0.3s ease;
        }}
        
        /* Workflow Runs */
        .runs-list {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}
        
        .run-item {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            transition: all 0.3s ease;
        }}
        
        .run-item:hover {{
            border-color: var(--border-hover);
        }}
        
        .run-status {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        
        .run-status.success {{ background: var(--success); }}
        .run-status.running {{ background: var(--info); animation: pulse 2s infinite; }}
        .run-status.failed {{ background: var(--error); }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .run-info {{ flex: 1; }}
        
        .run-name {{
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--text);
            transition: all 0.3s ease;
        }}
        
        .run-meta {{
            font-size: 0.75rem;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }}
        
        .run-time {{
            font-size: 0.875rem;
            color: var(--text-secondary);
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
        
        /* Skeleton */
        .skeleton {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 8px;
            animation: pulse 1.5s infinite;
            transition: all 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="header-content">
                <div>
                    <h1 class="header-title">⚡ Workflows</h1>
                    <p class="header-subtitle">Orchestrate and monitor your background workflows</p>
                </div>
                <button class="theme-toggle" id="theme-toggle" title="Toggle theme">
                    <svg class="moon-icon" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg>
                    <svg class="sun-icon" viewBox="0 0 24 24"><path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM2 13h2a1 1 0 0 0 0-2H2a1 1 0 0 0 0 2zm18 0h2a1 1 0 0 0 0-2h-2a1 1 0 0 0 0 2zM11 2v2a1 1 0 0 0 2 0V2a1 1 0 0 0-2 0zm0 18v2a1 1 0 0 0 2 0v-2a1 1 0 0 0-2 0zM5.99 4.58a1 1 0 1 0-1.41 1.41l1.06 1.06a1 1 0 1 0 1.41-1.41L5.99 4.58zm12.37 12.37a1 1 0 1 0-1.41 1.41l1.06 1.06a1 1 0 1 0 1.41-1.41l-1.06-1.06zm1.06-10.96a1 1 0 1 0-1.41-1.41l-1.06 1.06a1 1 0 1 0 1.41 1.41l1.06-1.06zM7.05 18.36a1 1 0 1 0-1.41-1.41l-1.06 1.06a1 1 0 1 0 1.41 1.41l1.06-1.06z"/></svg>
                </button>
            </div>
        </header>
        
        <div class="dashboard-grid">
            <!-- Engine Status -->
            <div class="section-card wide">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">⚙️</div>
                        Workflow Engine
                    </div>
                    <span class="badge" id="engine-badge">Loading...</span>
                </div>
                <div class="section-content">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                        <div id="engine-details">
                            <div class="skeleton" style="height: 250px;"></div>
                        </div>
                        <div>
                            <h3 style="font-size: 1rem; font-weight: 600; margin-bottom: 1rem; color: var(--text-secondary); transition: all 0.3s ease;">Available Engines</h3>
                            <div class="engine-options">
                                <div class="engine-option" id="opt-temporal">
                                    <div class="engine-option-icon">⏳</div>
                                    <div class="engine-option-name">Temporal</div>
                                </div>
                                <div class="engine-option" id="opt-prefect">
                                    <div class="engine-option-icon">🐦</div>
                                    <div class="engine-option-name">Prefect</div>
                                </div>
                                <div class="engine-option" id="opt-dagster">
                                    <div class="engine-option-icon">🎯</div>
                                    <div class="engine-option-name">Dagster</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Stats -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">📊</div>
                        Statistics
                    </div>
                </div>
                <div class="section-content">
                    <div class="stats-grid" id="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">-</div>
                            <div class="stat-label">Total Runs</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">-</div>
                            <div class="stat-label">Success</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">-</div>
                            <div class="stat-label">Failed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">-</div>
                            <div class="stat-label">Running</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Runs -->
            <div class="section-card">
                <div class="section-header">
                    <div class="section-title">
                        <div class="section-icon">📝</div>
                        Recent Runs
                    </div>
                </div>
                <div class="section-content">
                    <div class="runs-list" id="runs-list">
                        <div class="empty-state">
                            <div class="empty-icon">📝</div>
                            <p>No recent workflow runs</p>
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
        
        // Load saved theme or default to dark
        const savedTheme = localStorage.getItem('workflows-theme') || 'dark';
        html.setAttribute('data-theme', savedTheme);
        
        themeToggle.addEventListener('click', () => {{
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('workflows-theme', newTheme);
        }});
        
        async function loadState() {{
            try {{
                const res = await fetch(window.location.pathname + '/state');
                const data = await res.json();
                renderEngine(data.engine || {{}});
                renderRuns(data.runs || []);
            }} catch (e) {{
                console.error('Failed to load state:', e);
            }}
        }}
        
        function renderEngine(engine) {{
            document.getElementById('engine-badge').textContent = engine.enabled ? 'Active' : 'Inactive';
            
            // Update engine options
            document.querySelectorAll('.engine-option').forEach(opt => opt.classList.remove('active'));
            if (engine.engineName === 'temporal') document.getElementById('opt-temporal').classList.add('active');
            if (engine.engineName === 'prefect') document.getElementById('opt-prefect').classList.add('active');
            if (engine.engineName === 'dagster') document.getElementById('opt-dagster').classList.add('active');
            
            const container = document.getElementById('engine-details');
            
            const engineIcons = {{
                temporal: '⏳',
                prefect: '🐦',
                dagster: '🎯'
            }};
            
            container.innerHTML = `
                <div class="engine-card">
                    <div class="engine-icon">${{engineIcons[engine.engineName] || '⚙️'}}</div>
                    <div class="engine-name">${{engine.engineName ? engine.engineName.charAt(0).toUpperCase() + engine.engineName.slice(1) : 'Not Configured'}}</div>
                    <div class="engine-status ${{engine.enabled ? 'enabled' : 'disabled'}}">
                        ${{engine.enabled ? '✓ Enabled' : '✗ Disabled'}}
                    </div>
                    ${{engine.enabled ? `
                    <div class="engine-config">
                        ${{engine.temporal ? `
                            <div class="config-row">
                                <span class="config-label">Address</span>
                                <span class="config-value">${{engine.temporal}}</span>
                            </div>
                        ` : ''}}
                        ${{engine.prefect ? `
                            <div class="config-row">
                                <span class="config-label">API URL</span>
                                <span class="config-value">${{engine.prefect}}</span>
                            </div>
                        ` : ''}}
                        ${{engine.dagster ? `
                            <div class="config-row">
                                <span class="config-label">gRPC Endpoint</span>
                                <span class="config-value">${{engine.dagster}}</span>
                            </div>
                        ` : ''}}
                    </div>
                    ` : '<p style="color: var(--text-muted); margin-top: 1rem; transition: all 0.3s ease;">Configure a workflow engine to get started</p>'}}
                </div>
            `;
        }}
        
        function renderRuns(runs) {{
            const container = document.getElementById('runs-list');
            
            if (!runs.length) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <p>No recent workflow runs</p>
                    </div>
                `;
                return;
            }}
            
            container.innerHTML = runs.map(run => `
                <div class="run-item">
                    <div class="run-status ${{run.status}}"></div>
                    <div class="run-info">
                        <div class="run-name">${{run.name || 'Workflow Run'}}</div>
                        <div class="run-meta">${{run.id || 'Unknown ID'}}</div>
                    </div>
                    <div class="run-time">${{run.time || 'Just now'}}</div>
                </div>
            `).join('');
        }}
        
        loadState();
        setInterval(loadState, 8000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/state", response_class=JSONResponse, summary="Workflows state")
async def workflows_state() -> JSONResponse:
    """Return JSON snapshot of workflow engine configuration and sample runs."""
    cfg = _get_workflows_config()

    if cfg is None:
        engine_info: Dict[str, Any] = {
            "enabled": False,
            "engineName": None,
            "status": "Not configured",
        }
    else:
        engine_info = {
            "enabled": getattr(cfg, "enabled", False),
            "engineName": getattr(cfg, "engine", None),
            "temporal": f"{getattr(cfg, 'temporal_address', '')} / {getattr(cfg, 'temporal_namespace', '')}"
            if getattr(cfg, "engine", None) == "temporal"
            else None,
            "prefect": getattr(cfg, "prefect_api_url", "")
            if getattr(cfg, "engine", None) == "prefect"
            else None,
            "dagster": getattr(cfg, "dagster_grpc_endpoint", "")
            if getattr(cfg, "engine", None) == "dagster"
            else None,
        }

    runs: list[Dict[str, Any]] = []
    return JSONResponse({"engine": engine_info, "runs": runs})


__all__ = ["router"]
