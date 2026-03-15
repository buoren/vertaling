"""SQLAlchemyGlossary — glossary backed by a SQL database.

Requires: pip install "vertaling[sqlalchemy]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy import Table


def _default_glossary_table(metadata: Any) -> Table:
    """Create the default glossary terms table schema."""
    from sqlalchemy import Column, MetaData, String, Table

    if not isinstance(metadata, MetaData):
        msg = "metadata must be a sqlalchemy.MetaData instance"
        raise TypeError(msg)

    return Table(
        "vertaling_glossary_terms",
        metadata,
        Column("scope", String(256), primary_key=True, default=""),
        Column("source_locale", String(16), primary_key=True),
        Column("target_locale", String(16), primary_key=True),
        Column("source_term", String(256), primary_key=True),
        Column("target_term", String(256), nullable=False),
        extend_existing=True,
    )


class SQLAlchemyGlossary:
    """Glossary backed by a SQL database via SQLAlchemy Core.

    Args:
        session_factory: Callable returning a SQLAlchemy ``Session``.
        table: Optional custom SQLAlchemy ``Table``. If not provided,
            a default ``vertaling_glossary_terms`` table is created on
            the given metadata.
        metadata: SQLAlchemy ``MetaData`` for the default table. Required
            if ``table`` is not provided.

    Example::

        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.orm import sessionmaker
        from vertaling.glossaries.sqlalchemy import SQLAlchemyGlossary

        engine = create_engine("sqlite:///translations.db")
        metadata = MetaData()
        Session = sessionmaker(bind=engine)

        glossary = SQLAlchemyGlossary(session_factory=Session, metadata=metadata)
        metadata.create_all(engine)
    """

    def __init__(
        self,
        session_factory: Any,
        table: Table | None = None,
        metadata: Any | None = None,
    ) -> None:
        if table is not None:
            self._table = table
        elif metadata is not None:
            self._table = _default_glossary_table(metadata)
        else:
            msg = "Must provide either 'table' or 'metadata'"
            raise ValueError(msg)

        self._session_factory = session_factory

    @property
    def table(self) -> Table:
        """The underlying SQLAlchemy table."""
        return self._table

    def add_term(
        self,
        source_term: str,
        target_term: str,
        source_locale: str,
        target_locale: str,
        scope: str | None = None,
    ) -> None:
        """Add a single directional term mapping (upserts)."""
        t = self._table
        from sqlalchemy import select

        scope_val = scope or ""

        with self._session_factory() as session:
            existing = session.execute(
                select(t.c.source_term)
                .where(t.c.scope == scope_val)
                .where(t.c.source_locale == source_locale)
                .where(t.c.target_locale == target_locale)
                .where(t.c.source_term == source_term)
            ).first()

            if existing:
                session.execute(
                    t.update()
                    .where(t.c.scope == scope_val)
                    .where(t.c.source_locale == source_locale)
                    .where(t.c.target_locale == target_locale)
                    .where(t.c.source_term == source_term)
                    .values(target_term=target_term)
                )
            else:
                session.execute(
                    t.insert().values(
                        scope=scope_val,
                        source_locale=source_locale,
                        target_locale=target_locale,
                        source_term=source_term,
                        target_term=target_term,
                    )
                )
            session.commit()

    def add_equivalent_set(
        self,
        terms: dict[str, str],
        scope: str | None = None,
    ) -> None:
        """Add an equivalent term set across all language pairs.

        Example::

            glossary.add_equivalent_set({"en": "bird", "nl": "snoekje", "de": "Vogel"})

        Expands into all pair combinations automatically.
        """
        from itertools import permutations

        for source_locale, target_locale in permutations(terms, 2):
            self.add_term(
                terms[source_locale],
                terms[target_locale],
                source_locale,
                target_locale,
                scope=scope,
            )

    def get_terms(
        self,
        source_locale: str,
        target_locale: str,
        scopes: list[str] | None = None,
    ) -> dict[str, str]:
        """Return {source_term: target_term} for this pair.

        When *scopes* is provided, terms are merged in order so that later
        scopes override earlier ones.  When *scopes* is ``None``, only
        unscoped terms (scope = '') are returned.
        """
        t = self._table
        from sqlalchemy import select

        if scopes is None:
            stmt = (
                select(t.c.source_term, t.c.target_term)
                .where(t.c.scope == "")
                .where(t.c.source_locale == source_locale)
                .where(t.c.target_locale == target_locale)
            )
            with self._session_factory() as session:
                rows = session.execute(stmt).fetchall()
                return {row.source_term: row.target_term for row in rows}

        # Fetch all matching scopes in one query
        stmt = (
            select(t.c.scope, t.c.source_term, t.c.target_term)
            .where(t.c.scope.in_(scopes))
            .where(t.c.source_locale == source_locale)
            .where(t.c.target_locale == target_locale)
        )

        with self._session_factory() as session:
            rows = session.execute(stmt).fetchall()

        # Group by scope, then merge in the requested order
        by_scope: dict[str, dict[str, str]] = {}
        for row in rows:
            by_scope.setdefault(row.scope, {})[row.source_term] = row.target_term

        merged: dict[str, str] = {}
        for scope in scopes:
            merged.update(by_scope.get(scope, {}))
        return merged
