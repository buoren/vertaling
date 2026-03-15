"""Glossary stores for domain-specific term mappings."""

from vertaling.glossaries.base import Glossary
from vertaling.glossaries.memory import InMemoryGlossary

__all__ = ["Glossary", "InMemoryGlossary"]

# Optional store — only importable if sqlalchemy extra is installed:
#   from vertaling.glossaries.sqlalchemy import SQLAlchemyGlossary
