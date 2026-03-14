"""CompositeStore — internal helper that wraps multiple named stores."""

from __future__ import annotations

from vertaling._core.models import TranslationUnit
from vertaling.stores.base import TranslationStore


class CompositeStore:
    """Routes get/save across multiple named stores with read-only support.

    Not a ``TranslationStore`` itself — used internally by the pipeline.
    """

    def __init__(
        self,
        stores: dict[str, TranslationStore],
        read_only: set[str] | None = None,
        review_store: TranslationStore | None = None,
    ) -> None:
        if not stores:
            msg = "At least one store is required"
            raise ValueError(msg)
        self._stores = stores
        self._store_order = list(stores.keys())
        self._read_only = read_only or set()
        self._review_store = review_store

    def get(
        self,
        code: str,
        source_locale: str,
        target_locale: str,
        preferred_store: str | None = None,
    ) -> tuple[str | None, str | None]:
        """Look up a translation across stores.

        Returns (translated_text, store_name) — store_name is the store
        where the hit was found, or None on miss.
        """
        order = self._lookup_order(preferred_store)
        for name in order:
            result = self._stores[name].get(code, source_locale, target_locale)
            if result is not None:
                return result, name
        return None, None

    def save(self, unit: TranslationUnit, store_name: str | None = None) -> None:
        """Save a unit to the specified store, respecting read-only rules.

        If the target store is read-only, the unit goes to the review store.
        If no review store is configured, raises ``RuntimeError``.
        """
        target = store_name or self._store_order[0]

        if target in self._read_only:
            if self._review_store is None:
                msg = f"Store '{target}' is read-only and no review_store is configured"
                raise RuntimeError(msg)
            self._review_store.save(unit)
            return

        self._stores[target].save(unit)

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        """Aggregate pending units from all stores, tagging each with its store name."""
        results: list[TranslationUnit] = []
        for name, store in self._stores.items():
            units = store.get_pending(target_locales)
            for unit in units:
                unit.store = name
            results.extend(units)
        return results

    def get_failed(self) -> list[TranslationUnit]:
        """Aggregate failed units from all stores, tagging each with its store name."""
        results: list[TranslationUnit] = []
        for name, store in self._stores.items():
            units = store.get_failed()
            for unit in units:
                unit.store = name
            results.extend(units)
        return results

    def _lookup_order(self, preferred: str | None) -> list[str]:
        """Return store names in lookup order: preferred first, then the rest."""
        if preferred is None:
            return self._store_order
        if preferred not in self._stores:
            msg = f"Unknown store: '{preferred}'"
            raise KeyError(msg)
        return [preferred] + [n for n in self._store_order if n != preferred]
