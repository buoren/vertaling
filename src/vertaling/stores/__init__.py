"""Translation stores for persisting translations."""

from vertaling.stores.base import TranslationStore
from vertaling.stores.composite import CompositeStore
from vertaling.stores.json_file import JsonFileStore
from vertaling.stores.memory import InMemoryTranslationStore

__all__ = ["CompositeStore", "InMemoryTranslationStore", "JsonFileStore", "TranslationStore"]

# Optional stores — only importable if their extras are installed:
#   from vertaling.stores.sqlalchemy import SQLAlchemyStore
