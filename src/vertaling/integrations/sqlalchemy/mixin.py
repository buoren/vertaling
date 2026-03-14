"""TranslatableMixin — SQLAlchemy mixin for translation-aware ORM models."""

from __future__ import annotations

import copy
from typing import Any, ClassVar

from vertaling.stores.base import TranslationStore
from vertaling.utilities.codes import make_translation_code
from vertaling.utilities.json_path import get_at_path, resolve_wildcard_paths, set_at_path

# A field spec is either a plain column name ("name") or a tuple of
# (column_name, json_path_pattern) for JSON columns with wildcards.
FieldSpec = str | tuple[str, str]


class TranslatableMixin:
    """Mixin that adds translation-aware methods to SQLAlchemy models.

    Subclass this alongside your SQLAlchemy ``Base`` and declare which
    fields are translatable::

        class Convention(Base, TranslatableMixin):
            __tablename__ = "conventions"

            translatable_fields: ClassVar[list[FieldSpec]] = [
                "name",
                "description",
                ("settings", "maps.*.name"),
            ]

    Then retrieve translated values via ``get_translated()`` or build
    a fully-translated dict with ``to_dict_translated()``.
    """

    translatable_fields: ClassVar[list[FieldSpec]] = []

    def get_translated(
        self,
        field_name: str,
        target_locale: str,
        store: TranslationStore,
        source_locale: str = "en",
    ) -> str | None:
        """Return the translated value of a plain column, or the source value.

        Args:
            field_name: Column name on this model.
            target_locale: Desired locale.
            store: Translation store to look up from.
            source_locale: Source locale for the lookup.

        Returns:
            Translated string, or source value if no translation exists.
        """
        source_value = getattr(self, field_name, None)
        if not isinstance(source_value, str):
            return source_value

        if target_locale == source_locale:
            return source_value

        code = make_translation_code(
            self.__tablename__,  # type: ignore[attr-defined]
            field_name,
            str(self.id),  # type: ignore[attr-defined]
        )
        translated = store.get(code, source_locale, target_locale)
        return translated if translated is not None else source_value

    def get_translated_json_field(
        self,
        column_name: str,
        json_path: str,
        target_locale: str,
        store: TranslationStore,
        source_locale: str = "en",
    ) -> Any:
        """Return a translated value from within a JSON column.

        Args:
            column_name: The JSON column name on this model.
            json_path: Dotted path within the JSON value (no wildcards).
            target_locale: Desired locale.
            store: Translation store to look up from.
            source_locale: Source locale for the lookup.

        Returns:
            Translated string, or the source value at that path.
        """
        json_data = getattr(self, column_name, None)
        if json_data is None:
            return None

        source_value = get_at_path(json_data, json_path)
        if not isinstance(source_value, str):
            return source_value

        if target_locale == source_locale:
            return source_value

        code = make_translation_code(
            self.__tablename__,  # type: ignore[attr-defined]
            column_name,
            str(self.id),  # type: ignore[attr-defined]
            json_path=json_path,
        )
        translated = store.get(code, source_locale, target_locale)
        return translated if translated is not None else source_value

    def to_dict_translated(
        self,
        target_locale: str,
        store: TranslationStore,
        source_locale: str = "en",
        fields: list[FieldSpec] | None = None,
    ) -> dict[str, Any]:
        """Build a dict with translated values for all translatable fields.

        Args:
            target_locale: Desired locale.
            store: Translation store to look up from.
            source_locale: Source locale for the lookup.
            fields: Override the class-level ``translatable_fields``.

        Returns:
            Dict mapping field names to their (possibly translated) values.
        """
        specs = fields if fields is not None else self.translatable_fields
        result: dict[str, Any] = {}

        for spec in specs:
            if isinstance(spec, str):
                # Plain column
                result[spec] = self.get_translated(spec, target_locale, store, source_locale)
            else:
                # JSON column with wildcard pattern
                column_name, pattern = spec
                json_data = getattr(self, column_name, None)
                if json_data is None:
                    result[column_name] = None
                    continue

                # Deep copy to avoid mutating the original
                translated_data = copy.deepcopy(json_data)

                if target_locale != source_locale:
                    resolved = resolve_wildcard_paths(json_data, pattern)
                    for concrete_path, source_value in resolved:
                        if not isinstance(source_value, str):
                            continue
                        code = make_translation_code(
                            self.__tablename__,  # type: ignore[attr-defined]
                            column_name,
                            str(self.id),  # type: ignore[attr-defined]
                            json_path=concrete_path,
                        )
                        translated = store.get(code, source_locale, target_locale)
                        if translated is not None:
                            set_at_path(translated_data, concrete_path, translated)

                result[column_name] = translated_data

        return result
