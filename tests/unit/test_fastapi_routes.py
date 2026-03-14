"""Tests for FastAPI translation routes."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vertaling.integrations.fastapi.routes import create_translation_router
from vertaling.stores.json_file import JsonFileStore
from vertaling.stores.memory import InMemoryTranslationStore


@pytest.fixture
def json_store(tmp_path):
    en = {"app": {"title": "Hello", "greeting": "Good morning"}, "footer": "Copyright"}
    nl = {"app": {"title": "Hallo", "greeting": "Goedemorgen"}, "footer": "Auteursrecht"}
    (tmp_path / "en.json").write_text(json.dumps(en))
    (tmp_path / "nl.json").write_text(json.dumps(nl))
    return JsonFileStore(tmp_path, source_locale="en")


@pytest.fixture
def app_with_json(json_store):
    app = FastAPI()
    router = create_translation_router(store=json_store, default_locale="en")
    app.include_router(router, prefix="/translations")
    return app


@pytest.fixture
def client(app_with_json):
    return TestClient(app_with_json)


class TestGetTranslations:
    def test_returns_all_for_locale(self, client):
        resp = client.get("/translations?locale=en")
        assert resp.status_code == 200
        data = resp.json()
        assert data["app.title"] == "Hello"
        assert data["app.greeting"] == "Good morning"
        assert data["footer"] == "Copyright"

    def test_returns_different_locale(self, client):
        resp = client.get("/translations?locale=nl")
        data = resp.json()
        assert data["app.title"] == "Hallo"

    def test_filters_by_prefix(self, client):
        resp = client.get("/translations?locale=en&prefix=app")
        data = resp.json()
        assert "app.title" in data
        assert "app.greeting" in data
        assert "footer" not in data

    def test_default_locale(self, client):
        resp = client.get("/translations")
        data = resp.json()
        assert data["app.title"] == "Hello"

    def test_missing_locale_returns_empty(self, client):
        resp = client.get("/translations?locale=fr")
        assert resp.json() == {}


class TestBulkTranslations:
    def test_returns_requested_keys(self, client):
        resp = client.post(
            "/translations/bulk?locale=en",
            json=["app.title", "footer"],
        )
        data = resp.json()
        assert data["app.title"] == "Hello"
        assert data["footer"] == "Copyright"

    def test_missing_key_falls_back_to_key(self, client):
        resp = client.post(
            "/translations/bulk?locale=en",
            json=["app.title", "nonexistent.key"],
        )
        data = resp.json()
        assert data["nonexistent.key"] == "nonexistent.key"

    def test_different_locale(self, client):
        resp = client.post(
            "/translations/bulk?locale=nl",
            json=["app.title"],
        )
        assert resp.json()["app.title"] == "Hallo"


class TestPlaceholders:
    def test_substitutes_placeholders(self, json_store):
        # Create store with placeholder in value
        app = FastAPI()
        store = InMemoryTranslationStore()
        from vertaling._core.models import TranslationStatus, TranslationUnit

        store.save(
            TranslationUnit(
                code="contact",
                source_locale="en",
                target_locale="en",
                source_text="Email {{contactEmail}} for help",
                translated_text="Email {{contactEmail}} for help",
                status=TranslationStatus.COMPLETE,
            )
        )

        router = create_translation_router(
            store=store,
            placeholders={"contactEmail": "hi@example.com"},
        )
        app.include_router(router, prefix="/t")
        client = TestClient(app)

        resp = client.post("/t/bulk?locale=en", json=["contact"])
        assert resp.json()["contact"] == "Email hi@example.com for help"

    def test_unknown_placeholder_kept(self):
        from vertaling.integrations.fastapi.routes import _substitute

        result = _substitute(
            {"k": "Hello {{unknown}}"},
            {"contactEmail": "a@b.com"},
        )
        assert result["k"] == "Hello {{unknown}}"


class TestMemoryStore:
    def test_get_returns_empty_for_store_without_keys(self):
        """InMemoryTranslationStore has no keys() method, returns empty."""
        app = FastAPI()
        store = InMemoryTranslationStore()
        router = create_translation_router(store=store)
        app.include_router(router, prefix="/t")
        client = TestClient(app)

        resp = client.get("/t?locale=en")
        assert resp.json() == {}
