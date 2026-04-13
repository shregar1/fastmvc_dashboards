"""Cross-cutting constants for FastDashboards."""

from __future__ import annotations

from typing import Final

# Embed signing
QUERY_PARAM_SIGNATURE: Final[str] = "sig"
QUERY_PARAM_EXPIRES: Final[str] = "exp"
QUERY_PARAM_TOKEN_ID: Final[str] = "tid"
QUERY_PARAM_THEME: Final[str] = "theme"
QUERY_PARAM_LOCALE: Final[str] = "locale"
ENCODING_UTF8: Final[str] = "utf-8"
SIGNING_ALGORITHM: Final[str] = "sha256"

# SEO / meta
ENV_PUBLIC_BASE_URL: Final[str] = "FASTMVC_PUBLIC_BASE_URL"
DEFAULT_SITE_NAME: Final[str] = "FastMVC"
DEFAULT_LOCALE: Final[str] = "en_US"
DEFAULT_OG_TYPE: Final[str] = "website"
DEFAULT_TWITTER_CARD: Final[str] = "summary_large_image"
DEFAULT_ROBOTS_PRIVATE: Final[str] = "noindex, nofollow"
DEFAULT_THEME_COLOR: Final[str] = "#020617"
MAX_DESCRIPTION_LENGTH: Final[int] = 320
META_CHARSET: Final[str] = "UTF-8"
OG_IMAGE_WIDTH: Final[int] = 1200
OG_IMAGE_HEIGHT: Final[int] = 630
JSONLD_SCHEMA_CONTEXT: Final[str] = "https://schema.org"
JSONLD_TYPE_WEBPAGE: Final[str] = "WebPage"
JSONLD_TYPE_SOFTWARE: Final[str] = "SoftwareApplication"
JSONLD_APP_CATEGORY: Final[str] = "DeveloperApplication"
JSONLD_OS: Final[str] = "Cross-platform"
FALLBACK_PROJECT_URL: Final[str] = "https://github.com/shregar1/fastMVC"

# Status values
STATUS_HEALTHY: Final[str] = "healthy"
STATUS_UNHEALTHY: Final[str] = "unhealthy"
STATUS_SKIPPED: Final[str] = "skipped"
STATUS_DISABLED: Final[str] = "disabled"
STATUS_IDLE: Final[str] = "idle"
STATUS_ACTIVE: Final[str] = "active"
STATUS_ERROR: Final[str] = "error"
STATUS_UNKNOWN: Final[str] = "unknown"

# Colors
COLOR_SUCCESS: Final[str] = "#22c55e"
COLOR_ERROR: Final[str] = "#ef4444"
COLOR_WARNING: Final[str] = "#eab308"
COLOR_NEUTRAL: Final[str] = "#94a3b8"

# Timeouts / intervals
REQUEST_TIMEOUT_SECONDS: Final[float] = 5.0
RABBITMQ_TIMEOUT_SECONDS: Final[float] = 3.0
AUTO_REFRESH_INTERVAL_MS: Final[int] = 10000
TRUNCATION_LIMIT: Final[int] = 50
MAX_BODY_PREVIEW_LENGTH: Final[int] = 400

# Router prefixes
ROUTER_PREFIX_API: Final[str] = "/dashboard/api"
ROUTER_PREFIX_HEALTH: Final[str] = "/dashboard"
ROUTER_PREFIX_QUEUES: Final[str] = "/dashboard/queues"
ROUTER_PREFIX_SECRETS: Final[str] = "/dashboard/secrets"
ROUTER_PREFIX_TENANTS: Final[str] = "/dashboard/tenants"
ROUTER_PREFIX_WORKFLOWS: Final[str] = "/dashboard/workflows"

# LocalStorage theme keys
LOCALSTORAGE_THEME_KEY_API: Final[str] = "theme"
LOCALSTORAGE_THEME_KEY_QUEUES: Final[str] = "queues-dashboard-theme"
LOCALSTORAGE_THEME_KEY_SECRETS: Final[str] = "theme"
LOCALSTORAGE_THEME_KEY_TENANTS: Final[str] = "tenants-dashboard-theme"
LOCALSTORAGE_THEME_KEY_WORKFLOWS: Final[str] = "workflows-theme"

# Workflow engines
ENGINE_TEMPORAL: Final[str] = "temporal"
ENGINE_PREFECT: Final[str] = "prefect"
ENGINE_DAGSTER: Final[str] = "dagster"

# Worker backends
WORKER_BACKEND_CELERY: Final[str] = "celery"
WORKER_BACKEND_RQ: Final[str] = "rq"
WORKER_BACKEND_DRAMATIQ: Final[str] = "dramatiq"

# Default resource key
DEFAULT_RESOURCE_KEY: Final[str] = "dashboard"

# JWT algorithm for Metabase
JWT_ALGORITHM_HS256: Final[str] = "HS256"

# Theme fragments
THEME_FRAGMENT_DARK: Final[str] = "#theme=night"
THEME_FRAGMENT_LIGHT: Final[str] = "#theme=day"

# Health dashboard env vars
ENV_MONGO_ENABLED: Final[str] = "MONGO_ENABLED"
ENV_CASSANDRA_ENABLED: Final[str] = "CASSANDRA_ENABLED"
ENV_SCYLLA_ENABLED: Final[str] = "SCYLLA_ENABLED"
ENV_DYNAMO_ENABLED: Final[str] = "DYNAMO_ENABLED"
ENV_COSMOS_ENABLED: Final[str] = "COSMOS_ENABLED"
ENV_ELASTICSEARCH_ENABLED: Final[str] = "ELASTICSEARCH_ENABLED"

# Health dashboard defaults
DEFAULT_MONGO_URI: Final[str] = "mongodb://localhost:27017"
DEFAULT_MONGO_DATABASE: Final[str] = "admin"
DEFAULT_CASSANDRA_HOST: Final[str] = "127.0.0.1"
DEFAULT_CASSANDRA_PORT: Final[int] = 9042
CASSANDRA_HEALTH_QUERY: Final[str] = "SELECT release_version FROM system.local"
DEFAULT_SCYLLA_PORT: Final[int] = 9042
DYNAMO_HEALTH_TABLE: Final[str] = "healthcheck"
DEFAULT_AWS_REGION: Final[str] = "us-east-1"
DEFAULT_COSMOS_ACCOUNT_URI: Final[str] = ""
DEFAULT_COSMOS_DATABASE: Final[str] = "fastmvc"
DEFAULT_ELASTICSEARCH_HOST: Final[str] = "http://localhost:9200"
POSTGRES_HEALTH_QUERY: Final[str] = "SELECT 1"

# Secrets dashboard
DEFAULT_SECRETS_HEALTH_NAME: Final[str] = "fastmvc/health"
ENV_SECRETS_HEALTH_CHECK: Final[str] = "SECRETS_HEALTH_CHECK_NAME"
ENV_EXAMPLE_FILENAME: Final[str] = ".env.example"
ENV_CURRENT_FILENAME: Final[str] = ".env"

# HTTP status threshold
HTTP_STATUS_SERVER_ERROR_THRESHOLD: Final[int] = 500

# HTML defaults
DEFAULT_HTML_LANG: Final[str] = "en"

# Truthy env values
TRUTHY_ENV_VALUES: frozenset[str] = frozenset({"1", "true", "yes", "on"})

# Max error length
MAX_ERROR_LENGTH: Final[int] = 200

# Metabase locale param
PARAM_LOCALE: Final[str] = "_locale"

# Grafana
GRAFANA_EMBED_PATH_TEMPLATE: Final[str] = "/d/{uid}/{slug}"
