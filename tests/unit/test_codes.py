"""Tests for translation code builder."""

from vertaling.utilities.codes import make_translation_code


class TestMakeTranslationCode:
    def test_plain_code(self) -> None:
        code = make_translation_code("conventions", "name", "conv-001")
        assert code == "conventions.name.conv-001"

    def test_json_path_code(self) -> None:
        result = make_translation_code(
            "conventions",
            "settings",
            "conv-001",
            json_path="maps.0.name",
        )
        assert result == "conventions.settings.conv-001;maps.0.name"

    def test_no_json_path(self) -> None:
        result = make_translation_code("events", "title", "evt-42")
        assert result == "events.title.evt-42"
        assert ";" not in result

    def test_special_chars_in_id(self) -> None:
        result = make_translation_code("users", "bio", "user@example.com")
        assert result == "users.bio.user@example.com"

    def test_numeric_id(self) -> None:
        result = make_translation_code("posts", "title", "123")
        assert result == "posts.title.123"

    def test_nested_json_path(self) -> None:
        result = make_translation_code(
            "events",
            "config",
            "e1",
            json_path="sections.0.items.2.label",
        )
        assert result == "events.config.e1;sections.0.items.2.label"
