"""SQLAlchemyStore — translation store backed by a SQL database.

Requires: pip install "vertaling[sqlalchemy]"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vertaling._core.models import TranslationStatus, TranslationUnit

if TYPE_CHECKING:
    from sqlalchemy import Table


def _default_table(metadata: Any) -> Table:
    """Create the default translations table schema."""
    from sqlalchemy import Column, MetaData, String, Table, Text

    if not isinstance(metadata, MetaData):
        msg = "metadata must be a sqlalchemy.MetaData instance"
        raise TypeError(msg)

    return Table(
        "vertaling_translations",
        metadata,
        Column("code", String(256), primary_key=True),
        Column("locale", String(16), primary_key=True),
        Column("source_locale", String(16), nullable=False, default="en"),
        Column("source_text", Text, nullable=False),
        Column("translated_text", Text, nullable=True),
        Column("status", String(20), nullable=False, default="pending"),
        Column("context", String(256), nullable=True),
        Column("error", Text, nullable=True),
        extend_existing=True,
    )


class SQLAlchemyStore:
    """Translation store backed by a SQL database via SQLAlchemy Core.

    Uses SQLAlchemy Core (not ORM) so it works with any existing schema.
    The default table has composite primary key ``(code, locale)``.

    Args:
        session_factory: Callable returning a SQLAlchemy ``Session``.
        table: Optional custom SQLAlchemy ``Table``. If not provided,
            a default ``translations`` table is created on the given metadata.
        metadata: SQLAlchemy ``MetaData`` for the default table. Required
            if ``table`` is not provided.

    Example::

        from sqlalchemy import create_engine, MetaData
        from sqlalchemy.orm import sessionmaker
        from vertaling.stores.sqlalchemy import SQLAlchemyStore

        engine = create_engine("sqlite:///translations.db")
        metadata = MetaData()
        Session = sessionmaker(bind=engine)

        store = SQLAlchemyStore(session_factory=Session, metadata=metadata)
        metadata.create_all(engine)  # create table if needed
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
            self._table = _default_table(metadata)
        else:
            msg = "Must provide either 'table' or 'metadata'"
            raise ValueError(msg)

        self._session_factory = session_factory

    @property
    def table(self) -> Table:
        """The underlying SQLAlchemy table."""
        return self._table

    def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
        """Look up a completed translation."""
        t = self._table
        from sqlalchemy import select

        stmt = (
            select(t.c.translated_text)
            .where(t.c.code == code)
            .where(t.c.locale == target_locale)
            .where(t.c.status == TranslationStatus.COMPLETE.value)
        )

        with self._session_factory() as session:
            row = session.execute(stmt).first()
            return row[0] if row else None

    def save(self, unit: TranslationUnit) -> None:
        """Upsert a translation unit."""
        t = self._table
        from sqlalchemy import select

        with self._session_factory() as session:
            existing = session.execute(
                select(t.c.code)
                .where(t.c.code == unit.code)
                .where(t.c.locale == unit.target_locale)
            ).first()

            if existing:
                session.execute(
                    t.update()
                    .where(t.c.code == unit.code)
                    .where(t.c.locale == unit.target_locale)
                    .values(
                        source_locale=unit.source_locale,
                        source_text=unit.source_text,
                        translated_text=unit.translated_text,
                        status=unit.status.value,
                        context=unit.context,
                        error=unit.error,
                    )
                )
            else:
                session.execute(
                    t.insert().values(
                        code=unit.code,
                        locale=unit.target_locale,
                        source_locale=unit.source_locale,
                        source_text=unit.source_text,
                        translated_text=unit.translated_text,
                        status=unit.status.value,
                        context=unit.context,
                        error=unit.error,
                    )
                )
            session.commit()

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        """Return all pending units for the given locales."""
        t = self._table
        from sqlalchemy import select

        stmt = (
            select(t)
            .where(t.c.status == TranslationStatus.PENDING.value)
            .where(t.c.locale.in_(target_locales))
        )

        with self._session_factory() as session:
            rows = session.execute(stmt).fetchall()
            return [self._row_to_unit(row) for row in rows]

    def delete(self, code: str) -> None:
        """Delete all translations for a given code (all locales)."""
        t = self._table

        with self._session_factory() as session:
            session.execute(t.delete().where(t.c.code == code))
            session.commit()

    def get_failed(self) -> list[TranslationUnit]:
        """Return all failed units."""
        t = self._table
        from sqlalchemy import select

        stmt = select(t).where(t.c.status == TranslationStatus.FAILED.value)

        with self._session_factory() as session:
            rows = session.execute(stmt).fetchall()
            return [self._row_to_unit(row) for row in rows]

    @staticmethod
    def _row_to_unit(row: Any) -> TranslationUnit:
        """Convert a database row to a TranslationUnit."""
        return TranslationUnit(
            code=row.code,
            source_locale=row.source_locale,
            target_locale=row.locale,
            source_text=row.source_text,
            translated_text=row.translated_text,
            status=TranslationStatus(row.status),
            context=row.context,
            error=row.error,
        )
