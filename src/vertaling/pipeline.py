"""TranslationPipeline — the main orchestrator with translate-on-miss."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import re

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.glossaries.base import Glossary
from vertaling.stores.base import TranslationStore
from vertaling.stores.composite import CompositeStore
from vertaling.translators.base import Translator

logger = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    """Aggregated statistics from a pipeline run."""

    total_units: int = 0
    complete: int = 0
    pending: int = 0
    failed: int = 0
    skipped: int = 0
    chars_translated: int = 0
    coverage_by_locale: dict[str, float] = field(default_factory=dict)


class TranslationPipeline:
    """Orchestrates translation with a translate-on-miss pattern.

    On ``get()``, looks up the translation in the store(s). If missing,
    translates via the backend and saves the result before returning.

    For batch operations, ``run()`` pulls pending units from the store(s),
    translates them, and saves the results.

    Supports multiple named stores with fallback, read-only stores, and
    a review store for read-only misses.

    Args:
        backend: The translator to use.
        config: Pipeline configuration.
        store: Single translation store (backward-compatible).
        stores: Dict of named stores for multi-store routing.
        read_only: Names of stores that should not be written to.
        review_store: Where translations go when the target store is read-only.

    Example::

        pipeline = TranslationPipeline(
            backend=EchoTranslator(),
            config=TranslationConfig(source_locale="en"),
            stores={"json": json_store, "sql": sql_store},
            read_only=["json"],
            review_store=review_store,
        )

        text = await pipeline.get("app.title", "Welcome", target_locale="nl", store="json")
    """

    def __init__(
        self,
        backend: Translator,
        config: TranslationConfig,
        store: TranslationStore | None = None,
        stores: dict[str, TranslationStore] | None = None,
        read_only: list[str] | None = None,
        review_store: TranslationStore | None = None,
        glossary: Glossary | None = None,
        glossary_scopes: list[str] | None = None,
    ) -> None:
        if store is not None and stores is not None:
            msg = "Cannot pass both 'store' and 'stores'"
            raise ValueError(msg)
        if store is None and stores is None:
            msg = "Must pass either 'store' or 'stores'"
            raise ValueError(msg)

        self.backend = backend
        self.config = config

        if store is not None:
            stores = {"default": store}

        self._composite = CompositeStore(
            stores=stores,  # type: ignore[arg-type]
            read_only=set(read_only) if read_only else None,
            review_store=review_store,
        )

        self._glossary = glossary
        self._glossary_scopes = glossary_scopes

        # Keep a reference for backward compat (tests use pipeline.store)
        self.store = store if store is not None else next(iter(stores.values()))  # type: ignore[union-attr]

    async def get(
        self,
        code: str,
        source_text: str,
        target_locale: str,
        context: str | None = None,
        store: str | None = None,
        source_locale: str | None = None,
    ) -> str:
        """Look up a translation, translating on miss.

        Args:
            code: Unique key for this translatable string.
            source_text: The source text to translate if not cached.
            target_locale: Target locale code.
            context: Optional context hint for the translator.
            store: Preferred store to look up first.
            source_locale: Override config source_locale for this call.

        Returns:
            The translated text, or source_text if fallback is enabled and
            translation fails.
        """
        effective_source = source_locale or self.config.source_locale

        cached, _found_in = self._composite.get(
            code, effective_source, target_locale, preferred_store=store
        )
        if cached is not None:
            return cached

        unit = TranslationUnit(
            code=code,
            source_locale=effective_source,
            target_locale=target_locale,
            source_text=source_text,
            context=context,
        )

        self._attach_glossary([unit])
        results = await self.backend.translate_batch([unit])
        self._enforce_glossary(results)
        translated = results[0]

        if translated.status == TranslationStatus.COMPLETE and translated.translated_text:
            self._composite.save(translated, store_name=store)
            return translated.translated_text

        translated.status = (
            translated.status
            if translated.status == TranslationStatus.FAILED
            else TranslationStatus.FAILED
        )
        self._composite.save(translated, store_name=store)

        if self.config.fallback_to_source:
            return source_text

        msg = translated.error or f"Translation failed for {code} -> {target_locale}"
        raise RuntimeError(msg)

    async def translate_batch(
        self,
        units: list[TranslationUnit],
        store: str | None = None,
    ) -> list[TranslationUnit]:
        """Translate a list of units directly via the backend.

        Saves results to the store. Useful for ad-hoc batch translation.
        """
        if not units:
            return []

        self._attach_glossary(units)
        results = await self.backend.translate_batch(units)
        self._enforce_glossary(results)
        for unit in results:
            self._composite.save(unit, store_name=store or unit.store)
        return results

    async def run(
        self,
        target_locales: list[str] | None = None,
    ) -> PipelineStats:
        """Run the batch pipeline: pull pending from all stores, translate, save.

        Args:
            target_locales: Override config target_locales for this run.

        Returns:
            PipelineStats with counts for this run.
        """
        locales = target_locales or self.config.target_locales
        pending = self._composite.get_pending(locales)

        stats = PipelineStats(total_units=len(pending))

        if not pending:
            return stats

        self._attach_glossary(pending)

        # Chunk into batches respecting translator char limit
        max_chars = self.backend.max_batch_chars()
        batches = self._chunk(pending, max_chars)

        for batch in batches:
            results = await self.backend.translate_batch(batch)
            self._enforce_glossary(results)
            for unit in results:
                self._composite.save(unit, store_name=unit.store)
                if unit.status == TranslationStatus.COMPLETE:
                    stats.complete += 1
                    stats.chars_translated += len(unit.source_text)
                elif unit.status == TranslationStatus.FAILED:
                    stats.failed += 1
                elif unit.status == TranslationStatus.SKIPPED:
                    stats.skipped += 1
                else:
                    stats.pending += 1

        return stats

    async def retry_failed(self) -> PipelineStats:
        """Retry all failed translations."""
        failed = self._composite.get_failed()
        for unit in failed:
            unit.status = TranslationStatus.PENDING
            unit.error = None
        return await self.translate_batch_and_stats(failed)

    async def translate_batch_and_stats(self, units: list[TranslationUnit]) -> PipelineStats:
        """Translate units and return stats."""
        stats = PipelineStats(total_units=len(units))
        if not units:
            return stats

        results = await self.translate_batch(units)
        for unit in results:
            if unit.status == TranslationStatus.COMPLETE:
                stats.complete += 1
                stats.chars_translated += len(unit.source_text)
            elif unit.status == TranslationStatus.FAILED:
                stats.failed += 1
            elif unit.status == TranslationStatus.SKIPPED:
                stats.skipped += 1
            else:
                stats.pending += 1
        return stats

    def _attach_glossary(self, units: list[TranslationUnit]) -> None:
        """Populate glossary_terms on each unit from the glossary."""
        if self._glossary is None:
            return

        # Cache terms by (source, target) pair to avoid repeated lookups
        cache: dict[tuple[str, str], dict[str, str]] = {}
        for unit in units:
            key = (unit.source_locale, unit.target_locale)
            if key not in cache:
                cache[key] = self._glossary.get_terms(
                    key[0], key[1], scopes=self._glossary_scopes
                )
            terms = cache[key]
            if terms:
                unit.glossary_terms = terms

    @staticmethod
    def _enforce_glossary(units: list[TranslationUnit]) -> None:
        """Post-process translated text to enforce glossary terms."""
        for unit in units:
            if (
                not unit.glossary_terms
                or unit.status != TranslationStatus.COMPLETE
                or not unit.translated_text
            ):
                continue

            text = unit.translated_text
            for source_term, target_term in unit.glossary_terms.items():
                text = re.sub(re.escape(source_term), target_term, text, flags=re.IGNORECASE)
            unit.translated_text = text

    @staticmethod
    def _chunk(units: list[TranslationUnit], max_chars: int) -> list[list[TranslationUnit]]:
        """Split units into batches respecting the character limit."""
        batches: list[list[TranslationUnit]] = []
        current_batch: list[TranslationUnit] = []
        current_chars = 0

        for unit in units:
            unit_chars = len(unit.source_text)
            if current_batch and current_chars + unit_chars > max_chars:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            current_batch.append(unit)
            current_chars += unit_chars

        if current_batch:
            batches.append(current_batch)

        return batches
