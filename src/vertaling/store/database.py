"""DatabasePipelineStore — persists pipeline state in the application database.

Schema (create via Alembic migration or SQLAlchemy create_all):

    translation_job
      id              UUID PK
      unit_id         VARCHAR(64)  -- stable hash, UNIQUE
      status          ENUM(pending, in_progress, complete, failed, skipped)
      source_text     TEXT
      source_locale   VARCHAR(10)
      target_locale   VARCHAR(10)
      translated_text TEXT NULL
      origin_type     ENUM(po, model_field)
      origin_meta     JSON
      created_at      TIMESTAMP
      updated_at      TIMESTAMP
      error           TEXT NULL
"""

from __future__ import annotations

from typing import Any

from vertaling._core.models import TranslationUnit


class DatabasePipelineStore:
    """Pipeline store backed by the application's existing SQLAlchemy session.

    Zero additional infrastructure — uses the same database as the application.

    Args:
        session: SQLAlchemy Session or async Session.
    """

    def __init__(self, session: Any) -> None: ...

    def get(self, unit_id: str) -> TranslationUnit | None:
        raise NotImplementedError

    def save(self, unit: TranslationUnit) -> None:
        raise NotImplementedError

    def pending(self) -> list[TranslationUnit]:
        raise NotImplementedError

    def failed(self) -> list[TranslationUnit]:
        raise NotImplementedError
