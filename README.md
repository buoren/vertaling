# vertaling

A decoupled translation pipeline with **translate-on-miss**. Your app owns its database — vertaling only knows about a simple `TranslationStore` protocol. When a lookup misses, vertaling translates via the configured translator and saves the result automatically.  It also supports bolt-on content translation for databases and other CMS storage which may or may not support localization.

## Installation

```bash
pip install vertaling                        # core
pip install "vertaling[fastapi]"             # FastAPI integration
pip install "vertaling[google]"              # Google Cloud Translate
pip install "vertaling[sqlalchemy]"          # SQLAlchemy store
pip install "vertaling[cli]"                 # CLI tools
pip install "vertaling[all]"                 # everything
```

## Quick start

```python
from vertaling import TranslationPipeline, TranslationConfig
from vertaling.translators import EchoTranslator
from vertaling.stores import InMemoryTranslationStore

pipeline = TranslationPipeline(
    backend=EchoTranslator(),
    config=TranslationConfig(source_locale="en", target_locales=["nl", "de"]),
    store=InMemoryTranslationStore(),
)

# Translate-on-miss: looks up "app.title" in the store.
# If not found, translates "Welcome" via the translator, saves it, and returns.
text = await pipeline.get("app.title", "Welcome", target_locale="nl")
```

## Core concepts

### TranslationStore (protocol)

Your app implements this protocol to connect vertaling to your database. Vertaling never touches your schema directly.

```python
from vertaling import TranslationStore, TranslationUnit

class MyStore:
    """Implements TranslationStore backed by your DB."""

    def get(self, code: str, source_locale: str, target_locale: str) -> str | None:
        row = db.query(Translation).filter_by(code=code, locale=target_locale).first()
        return row.value if row else None

    def save(self, unit: TranslationUnit) -> None:
        db.merge(Translation(code=unit.code, locale=unit.target_locale, value=unit.translated_text))
        db.commit()

    def get_pending(self, target_locales: list[str]) -> list[TranslationUnit]:
        # Return units that still need translation
        ...

    def get_failed(self) -> list[TranslationUnit]:
        # Return failed units eligible for retry
        ...
```

### Translator (protocol)

Translators handle the actual translation. Vertaling ships with:

| Translator | Extra | Description |
|---|---|---|
| `EchoTranslator` | — | Returns source text unchanged (testing) |
| `GoogleTranslator` | `[google]` | Google Cloud Translation API v3 |
| `LibreTranslator` | `[libretranslate]` | Self-hosted LibreTranslate |
| `HumanReviewTranslator` | — | Queues units for human review |

```python
from vertaling.translators.google import GoogleTranslator

translator = GoogleTranslator(project_id="my-gcp-project")
```

Custom translators just need to implement the `Translator` protocol:

```python
from vertaling import Translator, TranslationUnit

class MyTranslator:
    async def translate_batch(self, units: list[TranslationUnit]) -> list[TranslationUnit]:
        ...

    def max_batch_chars(self) -> int:
        return 50_000

    def supported_locales(self) -> set[str]:
        return set()  # empty = accepts anything
```

### Pipeline

The pipeline ties a translator and store together:

```python
pipeline = TranslationPipeline(
    backend=translator,
    config=TranslationConfig(
        source_locale="en",
        target_locales=["nl", "de", "fr"],
        fallback_to_source=True,       # return source text if translation fails
        batch_size_chars=50_000,
        retry_attempts=3,
    ),
    store=my_store,
)
```

**Single lookup** (translate-on-miss):

```python
text = await pipeline.get("app.greeting", "Good morning", target_locale="nl")
```

**Batch run** (e.g. cron job — translates all pending units):

```python
stats = await pipeline.run(target_locales=["nl", "de"])
print(f"Translated {stats.complete}/{stats.total_units} units")
```

**Retry failed**:

```python
stats = await pipeline.retry_failed()
```

### Multiple stores

Use `stores=` to register named stores with fallback, read-only protection, and a review store for gated writes:

```python
pipeline = TranslationPipeline(
    backend=translator,
    config=TranslationConfig(source_locale="en", target_locales=["nl", "de"]),
    stores={
        "json": json_file_store,   # checked translations from JSON files
        "sql": database_store,     # app database
    },
    read_only=["json"],            # json store won't be written to
    review_store=review_store,     # new translations for read-only stores go here
)
```

Lookup tries the preferred store first, then falls back to others in registration order:

```python
# Try json first, then sql. On miss, translate and save to review_store
# (because json is read-only).
text = await pipeline.get("app.title", "Welcome", target_locale="nl", store="json")

# Try sql first, then json. On miss, translate and save to sql (writable).
text = await pipeline.get("app.title", "Welcome", target_locale="nl", store="sql")
```

**Per-call source locale** — for content not authored in the config default:

```python
# This content was written in Dutch, translate it to German
text = await pipeline.get(
    "event.description", "Welkom bij het evenement",
    target_locale="de",
    source_locale="nl",
)
```

The single `store=` parameter still works for simple setups — it's treated as `{"default": store}` internally.

### Built-in stores

| Store | Extra | Description |
|---|---|---|
| `InMemoryTranslationStore` | — | Dict-backed, for testing |
| `JsonFileStore` | — | Read-only, reads `{locale}.json` files with nested-key flattening |
| `SQLAlchemyStore` | `[sqlalchemy]` | SQL-backed via SQLAlchemy Core |

```python
from vertaling.stores import JsonFileStore

# Reads en.json, nl.json, etc. from the directory
json_store = JsonFileStore("./translations")

# Use as a read-only store in a multi-store pipeline
pipeline = TranslationPipeline(
    backend=translator,
    config=config,
    stores={"json": json_store, "sql": db_store},
    read_only=["json"],
    review_store=review_store,
)
```

```python
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from vertaling.stores.sqlalchemy import SQLAlchemyStore

engine = create_engine("sqlite:///translations.db")
metadata = MetaData()
Session = sessionmaker(bind=engine)

store = SQLAlchemyStore(session_factory=Session, metadata=metadata)
metadata.create_all(engine)  # creates the translations table
```

## Utilities

Built into core — no extra dependencies needed.

### Locale code normalization

```python
from vertaling import normalize_for_api

normalize_for_api("en-US")   # → "en"    (region stripped)
normalize_for_api("zh-TW")   # → "zh-tw" (region preserved — Chinese Traditional)
normalize_for_api("pt-BR")   # → "pt-br" (region preserved — Brazilian Portuguese)
normalize_for_api("de")      # → "de"    (bare code unchanged)
```

### String interpolation

```python
from vertaling import interpolate

interpolate("+ {count} more", {"count": 3})
# → "+ 3 more"

interpolate("Page {current} of {total}", {"current": 1, "total": 5})
# → "Page 1 of 5"
```

### Locale fallback

```python
from vertaling import resolve_locale

resolve_locale("nl-NL", ["nl", "en", "de"])     # → "nl"   (language-only match)
resolve_locale("nl", ["nl-NL", "en-US"])         # → "nl-NL" (reverse match)
resolve_locale("fr-FR", ["en", "de"])            # → "en"   (default fallback)
```

### Completeness checker

```python
from vertaling import check_completeness

reports = check_completeness(
    store=my_store,
    source_locale="en",
    target_locales=["nl", "de"],
    known_codes=["app.title", "app.greeting", "app.logout"],
)

for r in reports:
    print(f"{r.locale}: {r.coverage:.0%} — missing: {r.missing_keys}")
# nl: 67% — missing: ['app.logout']
# de: 33% — missing: ['app.greeting', 'app.logout']
```

## FastAPI integration

```bash
pip install "vertaling[fastapi]"
```

```python
from vertaling.integrations.fastapi import LocaleMiddleware, get_locale, get_pipeline

# Middleware: detect locale from Accept-Language, ?lang=, or path
app.add_middleware(
    LocaleMiddleware,
    supported_locales=["en", "nl", "de"],
    default_locale="en",
)

# Dependency: get the current request locale
@app.get("/content/{id}")
async def get_content(locale: str = Depends(get_locale)):
    ...

# Dependency: get the pipeline (override with your instance)
app.dependency_overrides[get_pipeline] = lambda: my_pipeline

@app.get("/translate")
async def translate(pipeline = Depends(get_pipeline)):
    text = await pipeline.get("greeting", "Hello", target_locale="nl")
    return {"text": text}
```

### Translation-serving routes

Ready-made endpoints for serving translations to frontends:

```python
from vertaling.integrations.fastapi import create_translation_router

router = create_translation_router(
    store=my_store,
    default_locale="en",
    placeholders={"contactEmail": "hi@example.com"},  # optional {{key}} substitution
)
app.include_router(router, prefix="/translations")
# GET  /translations?locale=nl&prefix=app   → all keys for locale, filtered by prefix
# POST /translations/bulk?locale=nl          → fetch specific keys (JSON body: ["app.title", "footer"])
```

### Background translation

```python
from vertaling.integrations.fastapi import translate_in_background

@app.post("/content")
async def create_content(data: ContentCreate, background_tasks: BackgroundTasks):
    units = build_translation_units(data)
    background_tasks.add_task(translate_in_background, units=units, pipeline=my_pipeline)
```

## Configuration

All settings can be set via environment variables with the `VERTALING_` prefix:

```bash
VERTALING_SOURCE_LOCALE=en
VERTALING_TARGET_LOCALES='["nl","de","fr"]'
VERTALING_BACKEND=google
VERTALING_BACKEND_API_KEY=your-key
VERTALING_FALLBACK_TO_SOURCE=true
VERTALING_BATCH_SIZE_CHARS=50000
VERTALING_RETRY_ATTEMPTS=3
```

Or passed directly:

```python
config = TranslationConfig(
    source_locale="en",
    target_locales=["nl", "de"],
    backend="google",
    backend_api_key="your-key",
)
```

## License

MIT
