"""Tests for TranslatableMixin."""

from __future__ import annotations

from typing import Any, ClassVar

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.integrations.sqlalchemy.mixin import FieldSpec, TranslatableMixin
from vertaling.stores.memory import InMemoryTranslationStore


class FakeModel(TranslatableMixin):
    """Minimal model simulating SQLAlchemy ORM."""

    __tablename__ = "events"

    translatable_fields: ClassVar[list[FieldSpec]] = [
        "name",
        "description",
        ("settings", "maps.*.name"),
    ]

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        settings: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.settings = settings


@pytest.fixture()
def store() -> InMemoryTranslationStore:
    s = InMemoryTranslationStore()
    # Pre-load some translations
    s.save(
        TranslationUnit(
            code="events.name.e1",
            source_locale="en",
            target_locale="nl",
            source_text="Summer Fest",
            translated_text="Zomerfest",
            status=TranslationStatus.COMPLETE,
        )
    )
    s.save(
        TranslationUnit(
            code="events.settings.e1;maps.0.name",
            source_locale="en",
            target_locale="nl",
            source_text="Main Hall",
            translated_text="Hoofdzaal",
            status=TranslationStatus.COMPLETE,
        )
    )
    return s


@pytest.fixture()
def model() -> FakeModel:
    return FakeModel(
        id="e1",
        name="Summer Fest",
        description="A great event",
        settings={
            "maps": [
                {"name": "Main Hall", "capacity": 500},
                {"name": "Side Room", "capacity": 100},
            ]
        },
    )


class TestGetTranslated:
    def test_hit(self, model: FakeModel, store: InMemoryTranslationStore) -> None:
        result = model.get_translated("name", "nl", store)
        assert result == "Zomerfest"

    def test_miss_returns_source(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.get_translated("description", "nl", store)
        assert result == "A great event"

    def test_source_locale_returns_source(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.get_translated("name", "en", store)
        assert result == "Summer Fest"

    def test_non_string_value(self, store: InMemoryTranslationStore) -> None:
        m = FakeModel(id="e2", name="Test", description="Test")
        m.name = None  # type: ignore[assignment]
        result = m.get_translated("name", "nl", store)
        assert result is None


class TestGetTranslatedJsonField:
    def test_hit(self, model: FakeModel, store: InMemoryTranslationStore) -> None:
        result = model.get_translated_json_field("settings", "maps.0.name", "nl", store)
        assert result == "Hoofdzaal"

    def test_miss_returns_source(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.get_translated_json_field("settings", "maps.1.name", "nl", store)
        assert result == "Side Room"

    def test_source_locale_returns_source(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.get_translated_json_field("settings", "maps.0.name", "en", store)
        assert result == "Main Hall"

    def test_none_column(self, store: InMemoryTranslationStore) -> None:
        m = FakeModel(id="e2", name="Test", description="Test", settings=None)
        result = m.get_translated_json_field("settings", "maps.0.name", "nl", store)
        assert result is None

    def test_non_string_value(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.get_translated_json_field(
            "settings",
            "maps.0.capacity",
            "nl",
            store,
        )
        assert result == 500  # non-string, returned as-is


class TestToDictTranslated:
    def test_full_translation(self, model: FakeModel, store: InMemoryTranslationStore) -> None:
        result = model.to_dict_translated("nl", store)
        assert result["name"] == "Zomerfest"
        assert result["description"] == "A great event"  # no translation exists
        assert result["settings"]["maps"][0]["name"] == "Hoofdzaal"
        assert result["settings"]["maps"][1]["name"] == "Side Room"  # no translation

    def test_deep_copy_safety(self, model: FakeModel, store: InMemoryTranslationStore) -> None:
        result = model.to_dict_translated("nl", store)
        # Mutating the result should not affect the original model
        result["settings"]["maps"][0]["name"] = "MUTATED"
        assert model.settings["maps"][0]["name"] == "Main Hall"  # type: ignore[index]

    def test_custom_fields_override(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.to_dict_translated("nl", store, fields=["name"])
        assert "name" in result
        assert "description" not in result
        assert "settings" not in result

    def test_source_locale_no_translation(
        self,
        model: FakeModel,
        store: InMemoryTranslationStore,
    ) -> None:
        result = model.to_dict_translated("en", store)
        assert result["name"] == "Summer Fest"
        assert result["settings"]["maps"][0]["name"] == "Main Hall"

    def test_none_json_column(self, store: InMemoryTranslationStore) -> None:
        m = FakeModel(id="e2", name="Test", description="Test", settings=None)
        result = m.to_dict_translated("nl", store)
        assert result["settings"] is None
