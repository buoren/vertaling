# Changelog

All notable changes to this project will be documented in this file.

## [1.2.2] - 2026-03-17

### Added
- **Pipeline glossary support**: `TranslationPipeline` accepts `glossary` and `glossary_scopes` parameters; attaches terms to units before translation and enforces them via post-processing
- `glossary_terms` field on `TranslationUnit` so translators can use glossary terms natively
- `cleanup_orphans()` utility: finds and deletes orphaned translations in one call (requires store with `keys()` and `delete()`)
- `delete()` method on `SQLAlchemyStore`
- `detect_language()` async method on `GoogleTranslator` for language detection via Google Cloud Translation v3

## [1.2.1] - 2026-03-15

### Added
- **Scoped glossaries**: `add_term` and `add_equivalent_set` accept `scope` parameter; `get_terms` accepts `scopes` list for ordered merge with later-wins semantics
- `scope` column added to default `vertaling_glossary_terms` table schema (part of PK)

### Changed
- Renamed glossary package from `vertaling.glossary` to `vertaling.glossaries` for consistency with `vertaling.stores`

## [1.1.0] - 2026-03-15

### Added
- **Glossary support**: `Glossary` protocol, `InMemoryGlossary`, and `SQLAlchemyGlossary` for domain-specific term mappings with equivalent term sets
- **GoogleTranslator glossary integration**: `glossary_id` parameter to use Google Cloud Translation v3 glossaries

## [1.0.0] - 2026-03-15

### Added
- **Core pipeline** with translate-on-miss, batch runs, retry, multi-store routing
- **Stores**: `InMemoryTranslationStore`, `JsonFileStore`, `SQLAlchemyStore`
- **Translators**: `EchoTranslator`, `PseudoTranslator`, `GoogleTranslator`
- **Utilities**: locale normalization, string interpolation, completeness checker
- **JSON path utilities**: `get_at_path`, `set_at_path`, `resolve_wildcard_paths`
- **Translation code builder**: `make_translation_code`
- **TranslatableMixin**: SQLAlchemy mixin for translation-aware ORM models
- **ContentScanner**: discover missing translations across database content
- **Orphan detection**: `find_orphans` for translation cleanup
- **FastAPI integration**: `LocaleMiddleware`, `get_locale`/`get_pipeline` dependencies, translation-serving routes, `translate_on_write`/`translate_on_read` decorators, background translation helper
