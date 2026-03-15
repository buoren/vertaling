"""Glossary stores for domain-specific term mappings."""

from vertaling.glossary.base import Glossary
from vertaling.glossary.memory import InMemoryGlossary

__all__ = ["Glossary", "InMemoryGlossary"]

# Optional store — only importable if sqlalchemy extra is installed:
#   from vertaling.glossary.sqlalchemy import SQLAlchemyGlossary
