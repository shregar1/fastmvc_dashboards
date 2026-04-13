"""Production-grade HTML SEO for FastMVC dashboards and static pages.

Provides canonical URLs, Open Graph, Twitter Cards, theme color, and JSON-LD
(`WebPage` + `SoftwareApplication`) with safe defaults for **internal**
dashboards (`noindex, nofollow`). Switch to public indexing when mounting a
marketing or docs surface by passing :class:`PageSEO` with ``robots="index, follow"``.

Environment:

- ``FASTMVC_PUBLIC_BASE_URL`` — optional absolute origin (e.g. ``https://app.example.com``)
  used to build ``og:url`` and ``link[rel=canonical]`` when ``canonical_url`` is not set.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from html import escape
from typing import Any

from fast_dashboards.core.constants import (
    DEFAULT_LOCALE,
    DEFAULT_OG_TYPE,
    DEFAULT_ROBOTS_PRIVATE,
    DEFAULT_SITE_NAME,
    DEFAULT_THEME_COLOR,
    DEFAULT_TWITTER_CARD,
    ENV_PUBLIC_BASE_URL,
    FALLBACK_PROJECT_URL,
    JSONLD_APP_CATEGORY,
    JSONLD_OS,
    JSONLD_SCHEMA_CONTEXT,
    JSONLD_TYPE_SOFTWARE,
    JSONLD_TYPE_WEBPAGE,
    MAX_DESCRIPTION_LENGTH,
    META_CHARSET,
    OG_IMAGE_HEIGHT,
    OG_IMAGE_WIDTH,
)


def render_dashboard_inline_head(
    *, page_title: str, description: str, path: str
) -> str:
    """SEO ``<head>`` inner markup for inline HTML dashboards (OG, Twitter, JSON-LD)."""
    return render_seo_head(default_dashboard_seo(page_title, description, path=path))


__all__ = [
    "PageSEO",
    "default_dashboard_seo",
    "render_dashboard_inline_head",
    "render_seo_head",
    "robots_txt_private_dashboards",
    "robots_txt_public_site",
]


_WS = re.compile(r"\s+")


def _strip_ws(s: str) -> str:
    """Execute _strip_ws operation.

    Args:
        s: The s parameter.

    Returns:
        The result of the operation.
    """
    return _WS.sub(" ", s.strip())


def _json_ld_embed(data: dict[str, Any]) -> str:
    """Serialize JSON-LD for embedding in HTML (mitigate ``</script>`` breakouts)."""
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return raw.replace("</", "<\\/")


@dataclass(frozen=True)
class PageSEO:
    """Metadata bundle for ``<head>`` social and search tags.

    Attributes:
        title: Document title (also used for ``og:title`` / ``twitter:title``).
        description: Short summary (≤ ~160 chars recommended for SERP snippets).
        canonical_url: Absolute preferred URL; if omitted, derived from env + path.
        path: URL path for canonical fallback (e.g. ``/dashboard/queues``).
        site_name: Brand / site name for ``og:site_name``.
        locale: Open Graph locale (``en_US`` style).
        og_type: Open Graph type (``website``, ``article``, …).
        og_image_url: Absolute image URL for previews (1200×630 recommended).
        twitter_card: ``summary``, ``summary_large_image``, etc.
        twitter_site: ``@handle`` for site attribution (optional).
        robots: ``robots`` meta content (default keeps internal dashboards out of indexes).
        theme_color: PWA / mobile browser chrome hint.
        include_json_ld: Emit ``WebPage`` + ``SoftwareApplication`` structured data.
        extra_json_ld: Additional ``@graph`` nodes (merged into the JSON-LD script).

    """

    title: str
    description: str
    canonical_url: str | None = None
    path: str = "/"
    site_name: str = DEFAULT_SITE_NAME
    locale: str = DEFAULT_LOCALE
    og_type: str = DEFAULT_OG_TYPE
    og_image_url: str | None = None
    twitter_card: str = DEFAULT_TWITTER_CARD
    twitter_site: str | None = None
    robots: str = DEFAULT_ROBOTS_PRIVATE
    theme_color: str = DEFAULT_THEME_COLOR
    include_json_ld: bool = True
    extra_json_ld: tuple[dict[str, Any], ...] = field(default_factory=tuple)


def _absolute_url(path: str) -> str | None:
    """Execute _absolute_url operation.

    Args:
        path: The path parameter.

    Returns:
        The result of the operation.
    """
    base = (os.environ.get(ENV_PUBLIC_BASE_URL) or "").rstrip("/")
    if not base:
        return None
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"


def default_dashboard_seo(
    page_title: str,
    description: str,
    *,
    path: str = "/",
    canonical_url: str | None = None,
    og_image_url: str | None = None,
) -> PageSEO:
    """Sensible SEO for operational dashboards: **noindex** by default, full OG/Twitter for link previews."""
    return PageSEO(
        title=page_title,
        description=_strip_ws(description)[:MAX_DESCRIPTION_LENGTH],
        path=path,
        canonical_url=canonical_url or _absolute_url(path),
        og_image_url=og_image_url,
    )


def render_seo_head(seo: PageSEO) -> str:
    """Return inner ``<head>`` markup (no ``<head>`` wrapper): meta, link, optional JSON-LD."""
    title_e = escape(seo.title, quote=True)
    desc = _strip_ws(seo.description)
    desc_e = escape(desc, quote=True)
    site_e = escape(seo.site_name, quote=True)
    locale_e = escape(seo.locale, quote=True)
    og_type_e = escape(seo.og_type, quote=True)
    robots_e = escape(seo.robots, quote=True)
    theme_e = escape(seo.theme_color, quote=True)
    tw_card_e = escape(seo.twitter_card, quote=True)

    canonical = seo.canonical_url or _absolute_url(seo.path)
    canonical_e = escape(canonical, quote=True) if canonical else None

    lines: list[str] = [
        f'<meta charset="{META_CHARSET}" />',
        f"<title>{escape(seo.title)}</title>",
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />',
        f'<meta name="description" content="{desc_e}" />',
        f'<meta name="robots" content="{robots_e}" />',
        f'<meta name="theme-color" content="{theme_e}" />',
        '<meta name="format-detection" content="telephone=no" />',
        '<meta name="referrer" content="strict-origin-when-cross-origin" />',
        f'<meta property="og:site_name" content="{site_e}" />',
        f'<meta property="og:locale" content="{locale_e}" />',
        f'<meta property="og:type" content="{og_type_e}" />',
        f'<meta property="og:title" content="{title_e}" />',
        f'<meta property="og:description" content="{desc_e}" />',
    ]

    if canonical:
        lines.append(f'<meta property="og:url" content="{canonical_e}" />')
        lines.append(f'<link rel="canonical" href="{canonical_e}" />')

    if seo.og_image_url:
        img_e = escape(seo.og_image_url, quote=True)
        lines.append(f'<meta property="og:image" content="{img_e}" />')
        lines.append(f'<meta property="og:image:width" content="{OG_IMAGE_WIDTH}" />')
        lines.append(f'<meta property="og:image:height" content="{OG_IMAGE_HEIGHT}" />')

    lines.extend(
        [
            f'<meta name="twitter:card" content="{tw_card_e}" />',
            f'<meta name="twitter:title" content="{title_e}" />',
            f'<meta name="twitter:description" content="{desc_e}" />',
        ]
    )
    if seo.twitter_site:
        ts = escape(seo.twitter_site.strip(), quote=True)
        lines.append(f'<meta name="twitter:site" content="{ts}" />')
    if seo.og_image_url:
        img_e = escape(seo.og_image_url, quote=True)
        lines.append(f'<meta name="twitter:image" content="{img_e}" />')

    if seo.include_json_ld:
        graph: list[dict[str, Any]] = []
        if canonical:
            graph.append(
                {
                    "@type": JSONLD_TYPE_WEBPAGE,
                    "@id": f"{canonical}#webpage",
                    "url": canonical,
                    "name": seo.title,
                    "description": desc,
                    "isPartOf": {"@type": "WebSite", "name": seo.site_name},
                }
            )
        graph.append(
            {
                "@type": "SoftwareApplication",
                "name": "FastMVC",
                "applicationCategory": "DeveloperApplication",
                "operatingSystem": "Cross-platform",
                "description": "Production-grade FastAPI building blocks for Python.",
                "url": _absolute_url("/") or FALLBACK_PROJECT_URL,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            }
        )
        for extra in seo.extra_json_ld:
            graph.append(extra)
        payload = {"@context": JSONLD_SCHEMA_CONTEXT, "@graph": graph}
        ld = _json_ld_embed(payload)
        lines.append(f'<script type="application/ld+json">{ld}</script>')

    return "\n    ".join(lines)


def robots_txt_private_dashboards() -> str:
    """Disallow all crawlers — use for internal ops / admin dashboards."""
    return "User-agent: *\nDisallow: /\n"


def robots_txt_public_site(*, sitemap_url: str | None = None) -> str:
    """Permissive robots.txt for a public marketing or docs host."""
    lines = ["User-agent: *", "Allow: /", ""]
    if sitemap_url:
        lines.append(f"Sitemap: {sitemap_url}")
    return "\n".join(lines).rstrip() + "\n"
