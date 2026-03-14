"""TranslationPipeline — the main orchestrator with translate-on-miss."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.base import TranslationStore
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

    On ``get()``, looks up the translation in the store. If missing,
    translates via the backend and saves the result before returning.

    For batch operations, ``run()`` pulls pending units from the store,
    translates them, and saves the results.

    Args:
        backend: The translator to use.
        config: Pipeline configuration.
        store: Translation store (app-provided, implements TranslationStore protocol).

    Example::

        from vertaling import TranslationPipeline, TranslationConfig
        from vertaling.translators import EchoTranslator

        pipeline = TranslationPipeline(
            backend=EchoTranslator(),
            config=TranslationConfig(source_locale="en"),
            store=my_store,
        )

        # Translate-on-miss
        text = await pipeline.get("app.title", "Welcome", target_locale="nl")

        # Batch run
        stats = await pipeline.run(target_locales=["nl", "de"])
    """

    def __init__(
        self,
        backend: Translator,
        config: TranslationConfig,
        store: TranslationStore,
    ) -> None:
        self.backend = backend
        self.config = config
        self.store = store

    async def get(
        self,
        code: str,
        source_text: str,
        target_locale: str,
        context: str | None = None,
    ) -> str:
        """Look up a translation, translating on miss.

        Args:
            code: Unique key for this translatable string.
            source_text: The source text to translate if not cached.
            target_locale: Target locale code.
            context: Optional context hint for the translator.

        Returns:
            The translated text, or source_text if fallback is enabled and
            translation fails.
        """
        cached = self.store.get(code, self.config.source_locale, target_locale)
        if cached is not None:
            return cached

        unit = TranslationUnit(
            code=code,
            source_locale=self.config.source_locale,
            target_locale=target_locale,
            source_text=source_text,
            context=context,
        )

        results = await self.backend.translate_batch([unit])
        translated = results[0]

        if translated.status == TranslationStatus.COMPLETE and translated.translated_text:
            self.store.save(translated)
            return translated.translated_text

        translated.status = (
            translated.status
            if translated.status == TranslationStatus.FAILED
            else TranslationStatus.FAILED
        )
        self.store.save(translated)

        if self.config.fallback_to_source:
            return source_text

        msg = translated.error or f"Translation failed for {code} -> {target_locale}"
        raise RuntimeError(msg)

    async def translate_batch(
        self,
        units: list[TranslationUnit],
    ) -> list[TranslationUnit]:
        """Translate a list of units directly via the backend.

        Saves results to the store. Useful for ad-hoc batch translation.
        """
        if not units:
            return []

        results = await self.backend.translate_batch(units)
        for unit in results:
            self.store.save(unit)
        return results

    async def run(
        self,
        target_locales: list[str] | None = None,
    ) -> PipelineStats:
        """Run the batch pipeline: pull pending from store, translate, save.

        Args:
            target_locales: Override config target_locales for this run.

        Returns:
            PipelineStats with counts for this run.
        """
        locales = target_locales or self.config.target_locales
        pending = self.store.get_pending(locales)

        stats = PipelineStats(total_units=len(pending))

        if not pending:
            return stats

        # Chunk into batches respecting translator char limit
        max_chars = self.backend.max_batch_chars()
        batches = self._chunk(pending, max_chars)

        for batch in batches:
            results = await self.backend.translate_batch(batch)
            for unit in results:
                self.store.save(unit)
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
        failed = self.store.get_failed()
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
