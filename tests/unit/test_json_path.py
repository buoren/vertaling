"""Tests for JSON path utilities."""

from vertaling.utilities.json_path import get_at_path, resolve_wildcard_paths, set_at_path


class TestGetAtPath:
    def test_simple_dict(self) -> None:
        assert get_at_path({"name": "Alice"}, "name") == "Alice"

    def test_nested_dict(self) -> None:
        obj = {"user": {"profile": {"name": "Alice"}}}
        assert get_at_path(obj, "user.profile.name") == "Alice"

    def test_dict_with_list(self) -> None:
        obj = {"maps": [{"name": "Hall A"}, {"name": "Hall B"}]}
        assert get_at_path(obj, "maps.0.name") == "Hall A"
        assert get_at_path(obj, "maps.1.name") == "Hall B"

    def test_list_index(self) -> None:
        obj = {"items": ["a", "b", "c"]}
        assert get_at_path(obj, "items.1") == "b"

    def test_missing_key_returns_none(self) -> None:
        assert get_at_path({"a": 1}, "b") is None

    def test_missing_nested_key_returns_none(self) -> None:
        assert get_at_path({"a": {"b": 1}}, "a.c") is None

    def test_index_out_of_range_returns_none(self) -> None:
        assert get_at_path({"items": [1]}, "items.5") is None

    def test_invalid_index_returns_none(self) -> None:
        assert get_at_path({"items": [1]}, "items.abc") is None

    def test_path_through_scalar_returns_none(self) -> None:
        assert get_at_path({"a": 42}, "a.b") is None

    def test_none_root_returns_none(self) -> None:
        assert get_at_path(None, "a") is None


class TestSetAtPath:
    def test_simple_dict(self) -> None:
        obj = {"name": "Alice"}
        set_at_path(obj, "name", "Bob")
        assert obj["name"] == "Bob"

    def test_nested_dict(self) -> None:
        obj = {"user": {"name": "Alice"}}
        set_at_path(obj, "user.name", "Bob")
        assert obj["user"]["name"] == "Bob"

    def test_dict_with_list(self) -> None:
        obj = {"maps": [{"name": "Hall A"}, {"name": "Hall B"}]}
        set_at_path(obj, "maps.0.name", "Main Hall")
        assert obj["maps"][0]["name"] == "Main Hall"
        assert obj["maps"][1]["name"] == "Hall B"

    def test_missing_parent_is_noop(self) -> None:
        obj = {"a": 1}
        set_at_path(obj, "b.c", "value")
        assert obj == {"a": 1}

    def test_index_out_of_range_is_noop(self) -> None:
        obj = {"items": [1]}
        set_at_path(obj, "items.5", "value")
        assert obj == {"items": [1]}

    def test_path_through_scalar_is_noop(self) -> None:
        obj = {"a": 42}
        set_at_path(obj, "a.b", "value")
        assert obj == {"a": 42}


class TestResolveWildcardPaths:
    def test_single_wildcard(self) -> None:
        obj = {"maps": [{"name": "Hall A"}, {"name": "Hall B"}]}
        result = resolve_wildcard_paths(obj, "maps.*.name")
        assert result == [("maps.0.name", "Hall A"), ("maps.1.name", "Hall B")]

    def test_nested_wildcards(self) -> None:
        obj = {
            "sections": [
                {"items": [{"label": "X"}, {"label": "Y"}]},
                {"items": [{"label": "Z"}]},
            ]
        }
        result = resolve_wildcard_paths(obj, "sections.*.items.*.label")
        assert result == [
            ("sections.0.items.0.label", "X"),
            ("sections.0.items.1.label", "Y"),
            ("sections.1.items.0.label", "Z"),
        ]

    def test_empty_list(self) -> None:
        obj = {"maps": []}
        result = resolve_wildcard_paths(obj, "maps.*.name")
        assert result == []

    def test_wildcard_on_non_list(self) -> None:
        obj = {"maps": "not a list"}
        result = resolve_wildcard_paths(obj, "maps.*.name")
        assert result == []

    def test_wildcard_on_dict(self) -> None:
        obj = {"maps": {"a": 1}}
        result = resolve_wildcard_paths(obj, "maps.*.name")
        assert result == []

    def test_no_wildcard(self) -> None:
        obj = {"a": {"b": "value"}}
        result = resolve_wildcard_paths(obj, "a.b")
        assert result == [("a.b", "value")]

    def test_missing_path_returns_empty(self) -> None:
        obj = {"a": 1}
        result = resolve_wildcard_paths(obj, "b.*.c")
        assert result == []
