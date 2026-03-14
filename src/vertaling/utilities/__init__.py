"""Built-in utilities for common translation tasks."""

from vertaling.utilities.codes import make_translation_code
from vertaling.utilities.completeness import CompletenessReport, check_completeness
from vertaling.utilities.interpolation import interpolate
from vertaling.utilities.json_path import get_at_path, resolve_wildcard_paths, set_at_path
from vertaling.utilities.locale import normalize_for_api, resolve_locale
from vertaling.utilities.scanner import ContentScanner, ScanResult, ScanTarget, find_orphans

__all__ = [
    "CompletenessReport",
    "ContentScanner",
    "ScanResult",
    "ScanTarget",
    "check_completeness",
    "find_orphans",
    "get_at_path",
    "interpolate",
    "make_translation_code",
    "normalize_for_api",
    "resolve_locale",
    "resolve_wildcard_paths",
    "set_at_path",
]
