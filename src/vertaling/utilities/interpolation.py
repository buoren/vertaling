"""String interpolation for translated strings."""

from __future__ import annotations

import re

_PARAM_RE = re.compile(r"\{(\w+)\}")


def interpolate(template: str, params: dict[str, str | int | float]) -> str:
    """Replace ``{param}`` placeholders in a translated string.

    Args:
        template: The translated string with placeholders.
        params: Mapping of placeholder names to values.

    Returns:
        The interpolated string. Unknown placeholders are left as-is.

    Example::

        interpolate("+ {count} more", {"count": 3})
        # → "+ 3 more"

        interpolate("Page {current} of {total}", {"current": 1, "total": 5})
        # → "Page 1 of 5"
    """

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in params:
            return str(params[key])
        return match.group(0)

    return _PARAM_RE.sub(_replace, template)
