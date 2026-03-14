# vertaling

A unified translation pipeline for FastAPI applications.

Handles both **static UI strings** (`.po` files via Babel/gettext) and
**user-generated content** (translatable SQLAlchemy model fields) through
the same batch API abstraction — one pipeline, one configuration, one mental model.

## Installation

```bash
# Core library
pip install vertaling

# With FastAPI integration
pip install "vertaling[fastapi]"

# With DeepL backend
pip install "vertaling[deepl]"

# With CLI
pip install "vertaling[cli]"

# Everything
pip install "vertaling[all]"
```

## Quick Start

```python
from vertaling import TranslationPipeline, TranslationConfig
from vertaling.backends import DeepLBackend

pipeline = TranslationPipeline(
    backend=DeepLBackend(api_key="your-key"),
    config=TranslationConfig(target_locales=["nl", "de", "fr"]),
)
```

## Documentation

_Coming soon._

## License

MIT
