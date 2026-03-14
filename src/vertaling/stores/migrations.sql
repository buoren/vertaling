-- vertaling translations table
-- Compatible with SQLAlchemyStore's default schema.

CREATE TABLE IF NOT EXISTS vertaling_translations (
    code         VARCHAR(256)  NOT NULL,
    locale       VARCHAR(16)   NOT NULL,
    source_locale VARCHAR(16)  NOT NULL DEFAULT 'en',
    source_text  TEXT          NOT NULL,
    translated_text TEXT       NULL,
    status       VARCHAR(20)   NOT NULL DEFAULT 'pending',
    context      VARCHAR(256)  NULL,
    error        TEXT          NULL,
    PRIMARY KEY (code, locale)
);
