"""Theme / locale helpers for signed embed query strings (Grafana, generic HMAC embeds).

Metabase appearance is often fragment-based; see :class:`~fast_dashboards.providers.metabase.MetabaseEmbedProvider`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fast_dashboards.core.constants import QUERY_PARAM_LOCALE, QUERY_PARAM_THEME


@dataclass(frozen=True)
class EmbedThemeParams:
    """Appearance hints for dashboards that read ``theme`` / ``locale`` query parameters.

    Pass into :func:`fast_dashboards.embed_signing.sign_embed_url` via ``extra_params``
    or use :func:`theme_to_extra_params`.
    """

    appearance: Optional[Literal["light", "dark"]] = None
    locale: Optional[str] = None


def theme_to_extra_params(theme: EmbedThemeParams) -> dict[str, str]:
    """Map to flat query values (``theme``, ``locale``) merged into signed URLs."""
    out: dict[str, str] = {}
    if theme.appearance is not None:
        out[QUERY_PARAM_THEME] = theme.appearance
    if theme.locale:
        out[QUERY_PARAM_LOCALE] = theme.locale
    return out
