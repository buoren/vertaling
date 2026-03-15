# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

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
