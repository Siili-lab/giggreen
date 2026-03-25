-- GigGreen Database Schema
-- SQLite — swap to PostgreSQL for production (syntax-compatible)

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── Workers ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS workers (
  id               INTEGER  PRIMARY KEY AUTOINCREMENT,
  phone            TEXT     UNIQUE NOT NULL,
  name             TEXT,
  location         TEXT,
  bio              TEXT,
  availability     TEXT     DEFAULT 'full-time',   -- full-time | part-time | weekends
  green_categories TEXT     DEFAULT '[]',           -- JSON array e.g. '["Solar","E-Waste"]'
  impact_score     INTEGER  DEFAULT 0,
  level            INTEGER  DEFAULT 1,
  level_name       TEXT     DEFAULT 'Green Seed',
  is_active        INTEGER  DEFAULT 1,
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Employers ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employers (
  id           INTEGER  PRIMARY KEY AUTOINCREMENT,
  phone        TEXT     UNIQUE NOT NULL,
  company_name TEXT,
  contact_name TEXT,
  location     TEXT,
  sector       TEXT,
  is_active    INTEGER  DEFAULT 1,
  created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Gigs ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gigs (
  id              INTEGER  PRIMARY KEY AUTOINCREMENT,
  employer_id     INTEGER  REFERENCES employers(id),
  title           TEXT     NOT NULL,
  description     TEXT,
  category        TEXT     NOT NULL,
  location        TEXT     NOT NULL,
  pay_kes         INTEGER  NOT NULL,
  impact_points   INTEGER  DEFAULT 0,
  duration        TEXT,                              -- e.g. "3 days", "2 weeks"
  tools_required  TEXT,
  status          TEXT     DEFAULT 'open',           -- open | matched | in_progress | complete | cancelled
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Human Blueprint™ (extended gig metadata) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS blueprints (
  id              INTEGER  PRIMARY KEY AUTOINCREMENT,
  gig_id          INTEGER  REFERENCES gigs(id),
  employer_id     INTEGER  REFERENCES employers(id),
  problem_90days  TEXT,    -- Step 1
  day_in_life     TEXT,    -- Step 2
  green_outcome   TEXT,    -- Step 3
  language        TEXT,    -- Step 4
  values_text     TEXT,    -- Step 5
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Applications ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS applications (
  id          INTEGER  PRIMARY KEY AUTOINCREMENT,
  worker_id   INTEGER  REFERENCES workers(id),
  gig_id      INTEGER  REFERENCES gigs(id),
  status      TEXT     DEFAULT 'applied',  -- applied | matched | confirmed | in_progress | complete | rejected
  match_score INTEGER  DEFAULT 0,
  applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(worker_id, gig_id)
);

-- ── Payments ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
  id             INTEGER  PRIMARY KEY AUTOINCREMENT,
  gig_id         INTEGER  REFERENCES gigs(id),
  worker_id      INTEGER  REFERENCES workers(id),
  employer_id    INTEGER  REFERENCES employers(id),
  amount_kes     INTEGER  NOT NULL,
  at_transaction_id TEXT,
  status         TEXT     DEFAULT 'held',  -- held | released | failed | refunded
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  released_at    TIMESTAMP
);

-- ── OTPs ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS otps (
  id         INTEGER  PRIMARY KEY AUTOINCREMENT,
  phone      TEXT     NOT NULL,
  code       TEXT     NOT NULL,
  used       INTEGER  DEFAULT 0,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── SMS Log ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sms_log (
  id        INTEGER  PRIMARY KEY AUTOINCREMENT,
  phone     TEXT     NOT NULL,
  message   TEXT     NOT NULL,
  direction TEXT     NOT NULL,  -- outbound | inbound
  status    TEXT     DEFAULT 'sent',
  sent_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── USSD Sessions ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ussd_sessions (
  id           INTEGER  PRIMARY KEY AUTOINCREMENT,
  session_id   TEXT     UNIQUE NOT NULL,
  phone        TEXT     NOT NULL,
  level        INTEGER  DEFAULT 1,
  state        TEXT     DEFAULT 'main',
  data         TEXT     DEFAULT '{}',  -- JSON for multi-step state
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Indexes ───────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_workers_phone     ON workers(phone);
CREATE INDEX IF NOT EXISTS idx_workers_location  ON workers(location);
CREATE INDEX IF NOT EXISTS idx_gigs_status       ON gigs(status);
CREATE INDEX IF NOT EXISTS idx_gigs_category     ON gigs(category);
CREATE INDEX IF NOT EXISTS idx_gigs_location     ON gigs(location);
CREATE INDEX IF NOT EXISTS idx_applications_worker ON applications(worker_id);
CREATE INDEX IF NOT EXISTS idx_applications_gig    ON applications(gig_id);
CREATE INDEX IF NOT EXISTS idx_otps_phone        ON otps(phone);
CREATE INDEX IF NOT EXISTS idx_sms_log_phone     ON sms_log(phone);
