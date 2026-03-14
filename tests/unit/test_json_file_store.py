"""Tests for JsonFileStore — read-only JSON file backed store."""

from __future__ import annotations

import json
from pathlib import Path

from vertaling._core.models import TranslationStatus, TranslationUnit
from vertaling.stores.json_file import JsonFileStore


def _write_json(directory: Path, locale: str, data: dict) -> None:
    (directory / f"{locale}.json").write_text(json.dumps(data), encoding="utf-8")


class TestJsonFileGet:
    def test_returns_value_for_existing_key(self, tmp_path):
        _write_json(tmp_path, "en", {"app": {"title": "Hello"}})
        store = JsonFileStore(tmp_path)
        assert store.get("app.title", "en", "en") == "Hello"

    def test_returns_none_for_missing_key(self, tmp_path):
        _write_json(tmp_path, "en", {"app": {"title": "Hello"}})
        store = JsonFileStore(tmp_path)
        assert store.get("app.missing", "en", "en") is None

    def test_returns_none_for_missing_locale(self, tmp_path):
        _write_json(tmp_path, "en", {"app": {"title": "Hello"}})
        store = JsonFileStore(tmp_path)
        assert store.get("app.title", "en", "fr") is None

    def test_deeply_nested_keys(self, tmp_path):
        _write_json(tmp_path, "en", {"a": {"b": {"c": {"d": "deep"}}}})
        store = JsonFileStore(tmp_path)
        assert store.get("a.b.c.d", "en", "en") == "deep"

    def test_multiple_locales(self, tmp_path):
        _write_json(tmp_path, "en", {"greeting": "Hello"})
        _write_json(tmp_path, "nl", {"greeting": "Hallo"})
        store = JsonFileStore(tmp_path)
        assert store.get("greeting", "en", "en") == "Hello"
        assert store.get("greeting", "en", "nl") == "Hallo"

    def test_locale_with_region(self, tmp_path):
        _write_json(tmp_path, "en-US", {"title": "Hello"})
        store = JsonFileStore(tmp_path)
        assert store.get("title", "en-US", "en-US") == "Hello"


class TestJsonFileReadOnly:
    def test_save_is_noop(self, tmp_path):
        _write_json(tmp_path, "en", {"key": "val"})
        store = JsonFileStore(tmp_path)
        unit = TranslationUnit(
            code="key",
            source_locale="en",
            target_locale="en",
            source_text="val",
            translated_text="new",
            status=TranslationStatus.COMPLETE,
        )
        store.save(unit)
        # Original value unchanged
        assert store.get("key", "en", "en") == "val"

    def test_get_pending_returns_empty(self, tmp_path):
        _write_json(tmp_path, "en", {"key": "val"})
        store = JsonFileStore(tmp_path)
        assert store.get_pending(["en"]) == []

    def test_get_failed_returns_empty(self, tmp_path):
        _write_json(tmp_path, "en", {"key": "val"})
        store = JsonFileStore(tmp_path)
        assert store.get_failed() == []


class TestJsonFileIntrospection:
    def test_keys_returns_flattened_keys(self, tmp_path):
        _write_json(tmp_path, "en", {"app": {"a": "1", "b": "2"}, "other": "3"})
        store = JsonFileStore(tmp_path, source_locale="en")
        keys = store.keys()
        assert sorted(keys) == ["app.a", "app.b", "other"]

    def test_keys_for_specific_locale(self, tmp_path):
        _write_json(tmp_path, "en", {"a": "1"})
        _write_json(tmp_path, "nl", {"a": "1", "b": "2"})
        store = JsonFileStore(tmp_path)
        assert len(store.keys("nl")) == 2
        assert len(store.keys("en")) == 1

    def test_locales_returns_all_stems(self, tmp_path):
        _write_json(tmp_path, "en-US", {"a": "1"})
        _write_json(tmp_path, "nl-NL", {"a": "1"})
        store = JsonFileStore(tmp_path)
        assert sorted(store.locales()) == ["en-US", "nl-NL"]

    def test_reload_clears_cache(self, tmp_path):
        _write_json(tmp_path, "en", {"key": "old"})
        store = JsonFileStore(tmp_path)
        assert store.get("key", "en", "en") == "old"

        _write_json(tmp_path, "en", {"key": "new"})
        store.reload()
        assert store.get("key", "en", "en") == "new"


class TestJsonFileEdgeCases:
    def test_empty_directory(self, tmp_path):
        store = JsonFileStore(tmp_path)
        assert store.get("any", "en", "en") is None
        assert store.keys() == []
        assert store.locales() == []

    def test_nonexistent_directory(self, tmp_path):
        store = JsonFileStore(tmp_path / "does_not_exist")
        assert store.get("any", "en", "en") is None
        assert store.locales() == []

    def test_non_string_values_converted(self, tmp_path):
        _write_json(tmp_path, "en", {"count": 42, "active": True})
        store = JsonFileStore(tmp_path)
        assert store.get("count", "en", "en") == "42"
        assert store.get("active", "en", "en") == "True"
