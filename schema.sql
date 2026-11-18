-- TakaTrack database schema (SQLite).  Owner: Samia.
-- Need a new column/table? Ask Samia, so all three of you get the same schema.
-- Money is stored as whole taka (INTEGER) so there are no rounding errors.
-- The same tables work in PostgreSQL / MySQL with tiny syntax changes.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT    NOT NULL UNIQUE,
    password_hash  TEXT    NOT NULL,
    -- the RECURRING monthly budget: copied into every new month automatically
    monthly_budget INTEGER NOT NULL DEFAULT 0 CHECK (monthly_budget >= 0),
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name          TEXT    NOT NULL COLLATE NOCASE,          -- "food" = "Food"
    monthly_limit INTEGER CHECK (monthly_limit IS NULL OR monthly_limit > 0),
    limit_asked   INTEGER NOT NULL DEFAULT 0,               -- 1 = we already asked for a limit once
    UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    title       TEXT    NOT NULL,
    amount      INTEGER NOT NULL CHECK (amount > 0),
    spent_on    TEXT    NOT NULL,                           -- YYYY-MM-DD
    note        TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses (user_id, spent_on);

-- One row per user per month: base budget + what was carried over from last month.
CREATE TABLE IF NOT EXISTS monthly_budgets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year         INTEGER NOT NULL,
    month        INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    base_amount  INTEGER NOT NULL CHECK (base_amount >= 0),
    carried_over INTEGER NOT NULL DEFAULT 0 CHECK (carried_over >= 0),
    UNIQUE (user_id, year, month)
);

-- The user's month-end decision: how much of the leftover goes to next month / savings.
CREATE TABLE IF NOT EXISTS rollovers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    year       INTEGER NOT NULL,          -- the month that was closed
    month      INTEGER NOT NULL,
    leftover   INTEGER NOT NULL,
    carried    INTEGER NOT NULL DEFAULT 0 CHECK (carried >= 0),
    saved      INTEGER NOT NULL DEFAULT 0 CHECK (saved >= 0),
    created_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, year, month)          -- a month can only be closed once
);
