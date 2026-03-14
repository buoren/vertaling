"""Tests for ContentScanner."""

from __future__ import annotations

from typing import Any

import pytest

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.memory import InMemoryTranslationStore
from vertaling.utilities.scanner import ContentScanner, ScanTarget, find_orphans


@pytest.fixture()
def store() -> InMemoryTranslationStore:
    return InMemoryTranslationStore()


@pytest.fixture()
def scanner(store: InMemoryTranslationStore) -> ContentScanner:
    return ContentScanner(store, target_locales=["nl", "de"])


class TestScanPlainFields:
    def test_all_missing(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[{"id": "e1", "name": "Summer Fest"}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 2  # nl + de
        assert result.total_checked == 2
        assert result.already_translated == 0
        assert all(u.source_text == "Summer Fest" for u in result.missing)

    def test_partially_translated(
        self,
        store: InMemoryTranslationStore,
        scanner: ContentScanner,
    ) -> None:
        store.save(
            TranslationUnit(
                code="events.name.e1",
                source_locale="en",
                target_locale="nl",
                source_text="Summer Fest",
                translated_text="Zomerfest",
                status=TranslationStatus.COMPLETE,
            )
        )
        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[{"id": "e1", "name": "Summer Fest"}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 1  # only de
        assert result.already_translated == 1
        assert result.missing[0].target_locale == "de"

    def test_all_translated(self, store: InMemoryTranslationStore, scanner: ContentScanner) -> None:
        for locale in ["nl", "de"]:
            store.save(
                TranslationUnit(
                    code="events.name.e1",
                    source_locale="en",
                    target_locale=locale,
                    source_text="Summer Fest",
                    translated_text=f"translated-{locale}",
                    status=TranslationStatus.COMPLETE,
                )
            )
        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[{"id": "e1", "name": "Summer Fest"}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 0
        assert result.already_translated == 2

    def test_skips_none_values(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[{"id": "e1", "name": None}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 0
        assert result.total_checked == 0

    def test_skips_non_string_values(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=["count"],
                records=[{"id": "e1", "count": 42}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 0

    def test_valid_translation_units(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[{"id": "e1", "name": "Test"}],
            )
        ]
        result = scanner.scan(targets)
        unit = result.missing[0]
        assert unit.code == "events.name.e1"
        assert unit.source_locale == "en"
        assert unit.source_text == "Test"
        assert unit.status == TranslationStatus.PENDING


class TestScanJsonFields:
    def test_wildcard_fields(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=[("settings", "maps.*.name")],
                records=[
                    {
                        "id": "e1",
                        "settings": {"maps": [{"name": "Hall A"}, {"name": "Hall B"}]},
                    }
                ],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 4  # 2 maps × 2 locales
        codes = {u.code for u in result.missing}
        assert "events.settings.e1;maps.0.name" in codes
        assert "events.settings.e1;maps.1.name" in codes

    def test_skips_non_string_json_values(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=[("settings", "maps.*.capacity")],
                records=[
                    {
                        "id": "e1",
                        "settings": {"maps": [{"capacity": 500}]},
                    }
                ],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 0

    def test_none_json_column(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=[("settings", "maps.*.name")],
                records=[{"id": "e1", "settings": None}],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 0


class TestObjectRecords:
    def test_object_records(self, scanner: ContentScanner) -> None:
        class Record:
            def __init__(self) -> None:
                self.id = "e1"
                self.name = "Summer Fest"

        targets = [
            ScanTarget(
                table="events",
                fields=["name"],
                records=[Record()],
            )
        ]
        result = scanner.scan(targets)
        assert len(result.missing) == 2
        assert result.missing[0].source_text == "Summer Fest"


class TestAccurateCounts:
    def test_multiple_records_and_fields(self, scanner: ContentScanner) -> None:
        targets = [
            ScanTarget(
                table="events",
                fields=["name", "description"],
                records=[
                    {"id": "e1", "name": "Fest A", "description": "Desc A"},
                    {"id": "e2", "name": "Fest B", "description": "Desc B"},
                ],
            )
        ]
        result = scanner.scan(targets)
        # 2 records × 2 fields × 2 locales = 8
        assert result.total_checked == 8
        assert len(result.missing) == 8


class TestFindOrphans:
    def test_finds_orphaned_codes(self) -> None:
        class KeyableStore:
            def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
                return None

            def save(self, unit: Any) -> None:
                pass

            def get_pending(self, target_locales: list[str]) -> list[Any]:
                return []

            def get_failed(self) -> list[Any]:
                return []

            def keys(self) -> list[str]:
                return [
                    "events.name.e1",
                    "events.name.e2",
                    "events.description.e1",
                    "events.settings.e3;maps.0.name",
                    "other.name.x1",  # different table
                ]

        store = KeyableStore()
        orphans = find_orphans(store, "events", valid_ids={"e1"})
        assert sorted(orphans) == [
            "events.name.e2",
            "events.settings.e3;maps.0.name",
        ]

    def test_no_orphans(self) -> None:
        class KeyableStore:
            def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
                return None

            def save(self, unit: Any) -> None:
                pass

            def get_pending(self, target_locales: list[str]) -> list[Any]:
                return []

            def get_failed(self) -> list[Any]:
                return []

            def keys(self) -> list[str]:
                return ["events.name.e1"]

        orphans = find_orphans(KeyableStore(), "events", valid_ids={"e1"})
        assert orphans == []

    def test_store_without_keys(self, store: InMemoryTranslationStore) -> None:
        # InMemoryTranslationStore doesn't have keys() — should return []
        result = find_orphans(store, "events", valid_ids={"e1"})
        assert result == []
