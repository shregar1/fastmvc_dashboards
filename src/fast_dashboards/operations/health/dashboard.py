"""Visual health dashboard for core services with beautiful UI.

Provides a stunning HTML dashboard at `/dashboard/health` showing the
status of enabled infrastructure services.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from loguru import logger
from sqlalchemy import text

from ...core.registry import registry
from ...core.seo import render_dashboard_inline_head

# Lazy imports for datastores - resolved at runtime via registry
_datastore_classes: Dict[str, Any] = {}


def _get_datastore_class(name: str) -> Optional[Any]:
    """Get datastore class lazily via registry."""
    if name not in _datastore_classes:
        klass = registry.get_datastore_class(name)
        _datastore_classes[name] = klass
    return _datastore_classes[name]


def _truncate_text(text: str, limit: int) -> str:
    """Safely truncate text to a limit."""
    if len(text) <= limit:
        return text
    return text[0:limit]  # type: ignore


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _bool_env(name: str, default: str = "false") -> bool:
    """Execute _bool_env operation.

    Args:
        name: The name parameter.
        default: The default parameter.

    Returns:
        The result of the operation.
    """
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _check_postgres() -> Dict[str, Any]:
    """Execute _check_postgres operation.

    Returns:
        The result of the operation.
    """
    db_session = registry.get_db_session()
    enabled = db_session is not None
    status = "skipped"
    message = "Database not configured"
    icon = "🐘"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "PostgreSQL",
            "key": "postgres",
            "enabled": False,
            "status": status,
            "message": message,
            "icon": icon,
            "color": color,
        }

    try:
        db_session.execute(text("SELECT 1"))
        status = "healthy"
        message = "Connected"
        color = "#22c55e"
    except Exception as exc:
        logger.error(f"PostgreSQL health check failed: {exc}")
        status = "unhealthy"
        message = _truncate_text(f"{exc}", 50)
        color = "#ef4444"
    return {
        "name": "PostgreSQL",
        "key": "postgres",
        "enabled": True,
        "status": status,
        "message": message,
        "icon": icon,
        "color": color,
    }


def _check_redis() -> Dict[str, Any]:
    """Execute _check_redis operation.

    Returns:
        The result of the operation.
    """
    redis_session = registry.get_redis_session()
    enabled = redis_session is not None
    status = "skipped"
    message = "Redis not configured"
    icon = "⚡"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "Redis",
            "key": "redis",
            "enabled": False,
            "status": status,
            "message": message,
            "icon": icon,
            "color": color,
        }

    try:
        if redis_session.ping():
            status = "healthy"
            message = "Connected"
            color = "#22c55e"
        else:
            status = "unhealthy"
            message = "Ping failed"
            color = "#ef4444"
    except Exception as exc:
        logger.error(f"Redis health check failed: {exc}")
        status = "unhealthy"
        message = _truncate_text(f"{exc}", 50)
        color = "#ef4444"
    return {
        "name": "Redis",
        "key": "redis",
        "enabled": True,
        "status": status,
        "message": message,
        "icon": icon,
        "color": color,
    }


def _check_mongo() -> Dict[str, Any]:
    """Execute _check_mongo operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("MONGO_ENABLED", "false")
    icon = "🍃"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "MongoDB",
            "key": "mongo",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        MongoDocumentStore = _get_datastore_class("MongoDocumentStore")
        if MongoDocumentStore is None:
            return {
                "name": "MongoDB",
                "key": "mongo",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        store = MongoDocumentStore(
            uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            database=os.getenv("MONGO_DATABASE", "admin"),
        )
        store.connect()
        db = store.get_database()
        db.command("ping")
        store.disconnect()
        return {
            "name": "MongoDB",
            "key": "mongo",
            "enabled": True,
            "status": "healthy",
            "message": "Connected",
            "icon": icon,
            "color": "#22c55e",
        }
    except Exception as exc:
        logger.error(f"MongoDB health check failed: {exc}")
        return {
            "name": "MongoDB",
            "key": "mongo",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _check_cassandra() -> Dict[str, Any]:
    """Execute _check_cassandra operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("CASSANDRA_ENABLED", "false")
    icon = "🔱"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "Cassandra",
            "key": "cassandra",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        CassandraWideColumnStore = _get_datastore_class("CassandraWideColumnStore")
        if CassandraWideColumnStore is None:
            return {
                "name": "Cassandra",
                "key": "cassandra",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        store = CassandraWideColumnStore(
            contact_points=os.getenv("CASSANDRA_CONTACT_POINTS", "127.0.0.1").split(
                ","
            ),
            port=int(os.getenv("CASSANDRA_PORT", "9042")),
            keyspace=os.getenv("CASSANDRA_KEYSPACE"),
        )
        store.connect()
        store.execute("SELECT release_version FROM system.local")
        store.disconnect()
        return {
            "name": "Cassandra",
            "key": "cassandra",
            "enabled": True,
            "status": "healthy",
            "message": "Connected",
            "icon": icon,
            "color": "#22c55e",
        }
    except Exception as exc:
        logger.error(f"Cassandra health check failed: {exc}")
        return {
            "name": "Cassandra",
            "key": "cassandra",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _check_scylla() -> Dict[str, Any]:
    """Execute _check_scylla operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("SCYLLA_ENABLED", "false")
    icon = "🌊"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "ScyllaDB",
            "key": "scylla",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        ScyllaWideColumnStore = _get_datastore_class("ScyllaWideColumnStore")
        if ScyllaWideColumnStore is None:
            return {
                "name": "ScyllaDB",
                "key": "scylla",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        store = ScyllaWideColumnStore(
            contact_points=os.getenv("SCYLLA_CONTACT_POINTS", "127.0.0.1").split(","),
            port=int(os.getenv("SCYLLA_PORT", "9042")),
            keyspace=os.getenv("SCYLLA_KEYSPACE"),
        )
        store.connect()
        store.execute("SELECT release_version FROM system.local")
        store.disconnect()
        return {
            "name": "ScyllaDB",
            "key": "scylla",
            "enabled": True,
            "status": "healthy",
            "message": "Connected",
            "icon": icon,
            "color": "#22c55e",
        }
    except Exception as exc:
        logger.error(f"ScyllaDB health check failed: {exc}")
        return {
            "name": "ScyllaDB",
            "key": "scylla",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _check_dynamo() -> Dict[str, Any]:
    """Execute _check_dynamo operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("DYNAMO_ENABLED", "false")
    icon = "📦"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "DynamoDB",
            "key": "dynamo",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        DynamoKeyValueStore = _get_datastore_class("DynamoKeyValueStore")
        if DynamoKeyValueStore is None:
            return {
                "name": "DynamoDB",
                "key": "dynamo",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        store = DynamoKeyValueStore(
            table_name="healthcheck",
            region_name=os.getenv("DYNAMO_REGION", "us-east-1"),
        )
        store.connect()
        store.disconnect()
        return {
            "name": "DynamoDB",
            "key": "dynamo",
            "enabled": True,
            "status": "healthy",
            "message": f"Region: {os.getenv('DYNAMO_REGION', 'us-east-1')}",
            "icon": icon,
            "color": "#22c55e",
        }
    except Exception as exc:
        logger.error(f"DynamoDB health check failed: {exc}")
        return {
            "name": "DynamoDB",
            "key": "dynamo",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _check_cosmos() -> Dict[str, Any]:
    """Execute _check_cosmos operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("COSMOS_ENABLED", "false")
    icon = "🌌"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "Cosmos DB",
            "key": "cosmos",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        CosmosDocumentStore = _get_datastore_class("CosmosDocumentStore")
        if CosmosDocumentStore is None:
            return {
                "name": "Cosmos DB",
                "key": "cosmos",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        store = CosmosDocumentStore(
            account_uri=os.getenv("COSMOS_ACCOUNT_URI", ""),
            account_key=os.getenv("COSMOS_ACCOUNT_KEY", ""),
            database=os.getenv("COSMOS_DATABASE", "fastmvc"),
        )
        store.connect()
        _ = store.get_database()
        store.disconnect()
        return {
            "name": "Cosmos DB",
            "key": "cosmos",
            "enabled": True,
            "status": "healthy",
            "message": "Connected",
            "icon": icon,
            "color": "#22c55e",
        }
    except Exception as exc:
        logger.error(f"Cosmos DB health check failed: {exc}")
        return {
            "name": "Cosmos DB",
            "key": "cosmos",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _check_elasticsearch() -> Dict[str, Any]:
    """Execute _check_elasticsearch operation.

    Returns:
        The result of the operation.
    """
    enabled = _bool_env("ELASTICSEARCH_ENABLED", "false")
    icon = "🔍"
    color = "#94a3b8"
    if not enabled:
        return {
            "name": "Elasticsearch",
            "key": "elasticsearch",
            "enabled": False,
            "status": "skipped",
            "message": "Disabled",
            "icon": icon,
            "color": color,
        }

    try:
        ElasticsearchSearchStore = _get_datastore_class("ElasticsearchSearchStore")
        if ElasticsearchSearchStore is None:
            return {
                "name": "Elasticsearch",
                "key": "elasticsearch",
                "enabled": True,
                "status": "unhealthy",
                "message": "Store not available",
                "icon": icon,
                "color": "#ef4444",
            }
        hosts = [
            h.strip()
            for h in os.getenv("ELASTICSEARCH_HOSTS", "http://localhost:9200").split(
                ","
            )
            if h.strip()
        ]
        store = ElasticsearchSearchStore(
            hosts=hosts,
            username=os.getenv("ELASTICSEARCH_USERNAME"),
            password=os.getenv("ELASTICSEARCH_PASSWORD"),
        )
        store.connect()
        healthy = store.ping()
        store.disconnect()
        status = "healthy" if healthy else "unhealthy"
        message = "Connected" if healthy else "Ping failed"
        color = "#22c55e" if healthy else "#ef4444"
        return {
            "name": "Elasticsearch",
            "key": "elasticsearch",
            "enabled": True,
            "status": status,
            "message": message,
            "icon": icon,
            "color": color,
        }
    except Exception as exc:
        logger.error(f"Elasticsearch health check failed: {exc}")
        return {
            "name": "Elasticsearch",
            "key": "elasticsearch",
            "enabled": True,
            "status": "unhealthy",
            "message": _truncate_text(f"{exc}", 50),
            "icon": icon,
            "color": "#ef4444",
        }


def _gather_services() -> List[Dict[str, Any]]:
    """Execute _gather_services operation.

    Returns:
        The result of the operation.
    """
    return [
        _check_postgres(),
        _check_redis(),
        _check_mongo(),
        _check_cassandra(),
        _check_scylla(),
        _check_dynamo(),
        _check_cosmos(),
        _check_elasticsearch(),
    ]


def _get_status_summary(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate status summary for visualization."""
    total = len(services)
    healthy = sum(1 for s in services if s["status"] == "healthy")
    unhealthy = sum(1 for s in services if s["status"] == "unhealthy")
    skipped = sum(1 for s in services if s["status"] == "skipped")
    enabled = sum(1 for s in services if s["enabled"])

    overall_status = (
        "healthy"
        if unhealthy == 0 and healthy > 0
        else "warning"
        if unhealthy == 0
        else "critical"
    )

    health_val: float = (healthy / enabled * 100.0) if enabled > 0 else 0.0
    return {
        "total": total,
        "healthy": healthy,
        "unhealthy": unhealthy,
        "skipped": skipped,
        "enabled": enabled,
        "overall_status": overall_status,
        "health_percent": round(health_val, 1),  # type: ignore
    }


@router.get("/health", response_class=HTMLResponse, summary="Health Dashboard")
async def health_dashboard() -> HTMLResponse:
    """Render a beautiful HTML dashboard showing health status."""
    services = _gather_services()
    summary = _get_status_summary(services)

    _head_seo = render_dashboard_inline_head(
        page_title="FastMVC Service Health",
        description="Live health checks for PostgreSQL, Redis, MongoDB, Elasticsearch, Cassandra, Scylla, DynamoDB, and Cosmos DB.",
        path="/dashboard/health",
    )

    # Build service cards
    service_cards = []
    for svc in services:
        pulse_animation = "pulse-animation" if svc["status"] == "healthy" else ""
        status_dot = f'<span class="status-dot {pulse_animation}" style="background: {svc["color"]};"></span>'
        card_html = f"""
        <div class="service-card" data-status="{svc["status"]}">
            <div class="service-header">
                <div class="service-icon">{svc["icon"]}</div>
                <div class="service-info">
                    <h3>{svc["name"]}</h3>
                    <span class="service-key">{svc["key"]}</span>
                </div>
                {status_dot}
            </div>
            <div class="service-body">
                <div class="status-badge" style="background: {svc["color"]}20; color: {svc["color"]}; border-color: {svc["color"]}40;">
                    {svc["status"].upper()}
                </div>
                <p class="service-message">{svc["message"]}</p>
            </div>
            <div class="service-footer">
                <span class="mode-badge">{"Enabled" if svc["enabled"] else "Disabled"}</span>
            </div>
        </div>
        """
        service_cards.append(card_html)

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
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html, body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
            transition: background 0.3s ease, color 0.3s ease;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Header */
        .header {{
            margin-bottom: 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            flex-wrap: wrap;
        }}
        
        .header-content {{
            flex: 1;
        }}
        
        .header-title {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}
        
        .header-title svg {{
            width: 32px;
            height: 32px;
            color: var(--text);
        }}
        
        .header-subtitle {{
            color: var(--text-secondary);
            font-size: 1rem;
            max-width: 600px;
        }}
        
        /* Theme Toggle */
        .theme-toggle {{
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px;
            cursor: pointer;
            color: var(--text-muted);
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .theme-toggle:hover {{
            background: var(--border);
            border-color: var(--border-hover);
            color: var(--text);
        }}
        
        .theme-toggle svg {{
            width: 20px;
            height: 20px;
        }}
        
        .theme-toggle .sun {{ display: none; }}
        .theme-toggle .moon {{ display: block; }}
        [data-theme="light"] .theme-toggle .sun {{ display: block; }}
        [data-theme="light"] .theme-toggle .moon {{ display: none; }}
        
        /* Summary Cards */
        .summary-section {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .summary-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .summary-card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }}
        
        .summary-card::before {{
            content: '';
            display: block;
            height: 3px;
            background: var(--border);
            border-radius: 3px;
            margin-bottom: 1rem;
        }}
        
        .summary-card.critical::before {{ background: var(--error); }}
        .summary-card.warning::before {{ background: var(--warning); }}
        .summary-card.healthy::before {{ background: var(--success); }}
        
        .summary-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: var(--text);
        }}
        
        .summary-label {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .summary-card.healthy .summary-value {{ color: var(--success); }}
        .summary-card.warning .summary-value {{ color: var(--warning); }}
        .summary-card.critical .summary-value {{ color: var(--error); }}
        
        /* Services Grid */
        .services-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        
        .service-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .service-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--text-muted);
            transition: all 0.3s ease;
        }}
        
        .service-card[data-status="healthy"]::before {{ background: var(--success); }}
        .service-card[data-status="unhealthy"]::before {{ background: var(--error); }}
        .service-card[data-status="skipped"]::before {{ background: var(--text-muted); }}
        
        .service-card:hover {{
            transform: translateY(-2px);
            border-color: var(--border-hover);
        }}
        
        .service-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        
        .service-icon {{
            font-size: 2rem;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--surface-raised);
            border-radius: 10px;
            border: 1px solid var(--border);
        }}
        
        .service-info {{
            flex: 1;
        }}
        
        .service-info h3 {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
            color: var(--text);
        }}
        
        .service-key {{
            font-size: 0.75rem;
            color: var(--text-muted);
            font-family: ui-monospace, monospace;
            text-transform: lowercase;
        }}
        
        .status-dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }}
        
        .pulse-animation {{
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .service-body {{
            margin-bottom: 1rem;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 0.375rem 0.75rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid;
            margin-bottom: 0.75rem;
        }}
        
        .service-message {{
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        
        .service-footer {{
            display: flex;
            justify-content: flex-end;
        }}
        
        .mode-badge {{
            font-size: 0.75rem;
            color: var(--text-muted);
            padding: 0.25rem 0.5rem;
            background: var(--surface-raised);
            border: 1px solid var(--border);
            border-radius: 4px;
        }}
        
        /* Refresh Indicator */
        .refresh-indicator {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 1.25rem;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }}
        
        .refresh-spinner {{
            width: 16px;
            height: 16px;
            border: 2px solid var(--border);
            border-top-color: var(--text-secondary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--border-hover);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .dashboard-container {{
                padding: 1rem;
            }}
            
            .header-title {{
                font-size: 1.5rem;
            }}
            
            .services-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <header class="header">
            <div class="header-content">
                <h1 class="header-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/>
                        <polyline points="12 22 12 15.5"/>
                        <polyline points="22 8.5 12 15.5 2 8.5"/>
                    </svg>
                    Service Health
                </h1>
                <p class="header-subtitle">Real-time monitoring of your infrastructure services and datastores</p>
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
        
        <section class="summary-section">
            <div class="summary-card {summary["overall_status"]}">
                <div class="summary-value">{summary["health_percent"]}%</div>
                <div class="summary-label">Health Score</div>
            </div>
            <div class="summary-card healthy">
                <div class="summary-value">{summary["healthy"]}</div>
                <div class="summary-label">Healthy</div>
            </div>
            <div class="summary-card critical">
                <div class="summary-value">{summary["unhealthy"]}</div>
                <div class="summary-label">Unhealthy</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary["skipped"]}</div>
                <div class="summary-label">Disabled</div>
            </div>
        </section>
        
        <div class="services-grid">
            {"" .join(service_cards)}
        </div>
    </div>
    
    <div class="refresh-indicator">
        <div class="refresh-spinner"></div>
        <span>Auto-refreshing...</span>
    </div>
    
    <script>
        // Theme management
        const themeToggle = document.getElementById('theme-toggle');
        const html = document.documentElement;
        
        const savedTheme = localStorage.getItem('theme') || 'dark';
        html.setAttribute('data-theme', savedTheme);
        
        themeToggle.addEventListener('click', () => {{
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        }});
        
        // Auto-refresh every 10 seconds
        setInterval(() => {{
            fetch(window.location.pathname)
                .then(response => response.text())
                .then(html => {{
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newGrid = doc.querySelector('.services-grid');
                    if (newGrid) {{
                        document.querySelector('.services-grid').innerHTML = newGrid.innerHTML;
                    }}
                    const newSummary = doc.querySelector('.summary-section');
                    if (newSummary) {{
                        document.querySelector('.summary-section').innerHTML = newSummary.innerHTML;
                    }}
                }})
                .catch(err => console.error('Refresh failed:', err));
        }}, 10000);
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)
