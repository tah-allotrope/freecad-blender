"""XML/HTML-safe text escaping shared by the SVG, DXF and PDF writers.

The real designs carry Vietnamese room names like ``BẾP & ĂN``; interpolating
them into SVG/HTML without escaping produces invalid XML (a bare ``&``) or
broken markup. Every text site uses :func:`escape_text` so authored names are
safe in both element content and attribute values.
"""
from __future__ import annotations

from xml.sax.saxutils import escape as _xml_escape

_ENTITIES = {'"': "&quot;", "'": "&apos;"}


def escape_text(value: object) -> str:
    """Return ``str(value)`` with ``&``, ``<``, ``>``, ``"`` and ``'`` replaced
    by their XML entities; the empty string when ``value`` is ``None``."""
    if value is None:
        return ""
    # `xml.sax.saxutils.escape` already escapes & < >; the entities dict adds
    # the two quote forms so the output is safe in attribute values too.
    return _xml_escape(str(value), _ENTITIES)
