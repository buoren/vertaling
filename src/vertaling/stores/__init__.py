"""Translation stores for persisting translations."""

from vertaling.stores.base import TranslationStore
from vertaling.stores.memory import InMemoryTranslationStore

__all__ = ["TranslationStore", "InMemoryTranslationStore"]
