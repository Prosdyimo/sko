-- V1: Initialschema fuer die Arbeitslosigkeitsdatenbank
-- Tabelle 1: Arbeitslosenquoten nach Altersgruppe und Sprachregion
CREATE TABLE IF NOT EXISTS altersgruppen_arbeitslosenquote (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    datum             TEXT    NOT NULL,   -- Format: YYYY-MM
    region            TEXT    NOT NULL,
    altersgruppe      TEXT    NOT NULL,
    arbeitslosenquote REAL    NOT NULL
);

-- Tabelle 2: Jugendarbeitslosenquoten nach Geschlecht und Sprachregion
CREATE TABLE IF NOT EXISTS jugendliche_arbeitslosenquote (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    datum             TEXT    NOT NULL,   -- Format: YYYY-MM
    region            TEXT    NOT NULL,
    geschlecht        TEXT    NOT NULL,
    arbeitslosenquote REAL    NOT NULL
);
