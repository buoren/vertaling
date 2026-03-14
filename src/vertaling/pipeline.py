"""TranslationPipeline — the main orchestrator."""

from __future__ import annotations

from dataclasses import dataclass

from vertaling._core.config import TranslationConfig
from vertaling._core.models import TranslationUnit
from vertaling.backends.base import TranslationBackend
from vertaling.collectors.base import Collector
from vertaling.store.base import PipelineStore
from vertaling.writers.base import Writer


@dataclass
class PipelineStats:
    """Aggregated statistics from a pipeline run or the current store state."""

    total_units: int = 0
    complete: int = 0
    pending: int = 0
    in_progress: int = 0
    failed: int = 0
    skipped: int = 0
    chars_translated: int = 0
    estimated_cost_eur: float = 0.0
    coverage_by_locale: dict[str, float] = None  # type: ignore[assignment]
    coverage_by_source: dict[str, float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.coverage_by_locale is None:
            self.coverage_by_locale = {}
        if self.coverage_by_source is None:
            self.coverage_by_source = {}


class TranslationPipeline:
    """Orchestrates collection, translation, and writing across all sources.

    The pipeline:
    1. Runs registered collectors to build a backlog of TranslationUnits
    2. Deduplicates units (same source_text + target_locale → one API call)
    3. Chunks units into batches respecting the backend's character limit
    4. Dispatches batches to the backend with retry/backoff
    5. Dispatches completed units to the appropriate writer
    6. Tracks all state in the pipeline store for idempotency

    Args:
        backend: The translation backend to use.
        config: Pipeline configuration.
        store: State store. Defaults to InMemoryPipelineStore if not provided.

    Example::

        from vertaling import TranslationPipeline, TranslationConfig
        from vertaling.backends import DeepLBackend
        from vertaling.collectors import PoFileCollector, ModelFieldCollector
        from vertaling.writers import PoFileWriter, ModelFieldWriter

        pipeline = TranslationPipeline(
            backend=DeepLBackend(api_key=settings.DEEPL_API_KEY),
            config=TranslationConfig(target_locales=["nl", "de"]),
        )
        pipeline.register_collector(po_collector, po_writer)
        pipeline.register_collector(model_collector, model_writer)

        await pipeline.run()
    """

    def __init__(
        self,
        backend: TranslationBackend,
        config: TranslationConfig,
        store: PipelineStore | None = None,
    ) -> None: ...

    def register_collector(self, collector: Collector, writer: Writer) -> None:
        """Register a (collector, writer) pair.

        The writer paired with a collector is called to write back results
        for units that originated from that collector.
        """
        raise NotImplementedError

    async def run(
        self,
        target_locales: list[str] | None = None,
        tenant_id: int | str | None = None,
        dry_run: bool = False,
    ) -> PipelineStats:
        """Run the full pipeline: collect → deduplicate → translate → write.

        Args:
            target_locales: Override config target_locales for this run.
            tenant_id: Restrict model field collection to this tenant.
            dry_run: Collect and report without calling the backend or writing.

        Returns:
            PipelineStats with counts and coverage for this run.
        """
        raise NotImplementedError

    async def translate_units(
        self,
        units: list[TranslationUnit],
    ) -> list[TranslationUnit]:
        """Translate a list of units without going through collectors/writers.

        Useful for translating ad-hoc content (e.g. from a background task).
        """
        raise NotImplementedError

    def stats(self) -> PipelineStats:
        """Return current stats from the pipeline store."""
        raise NotImplementedError
