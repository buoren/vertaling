"""SQLAlchemy integration helpers.

Requires: pip install "vertaling[sqlalchemy]"

Usage::

    from vertaling.integrations.sqlalchemy import TranslatableMixin
"""

from vertaling.integrations.sqlalchemy.mixin import TranslatableMixin

__all__ = [
    "TranslatableMixin",
]
