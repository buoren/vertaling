"""Built-in utilities for common translation tasks."""

from vertaling.utilities.completeness import CompletenessReport, check_completeness
from vertaling.utilities.interpolation import interpolate
from vertaling.utilities.locale import resolve_locale

__all__ = [
    "CompletenessReport",
    "check_completeness",
    "interpolate",
    "resolve_locale",
]
