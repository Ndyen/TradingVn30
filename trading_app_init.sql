-- trading_app_init.sql
-- PostgreSQL schema for VN30 Short-term Best Buy Finder (vnstock-based)
-- Encoding: UTF-8
-- Created: 2026-01-29
--
-- How to run:
--   psql -h <host> -U <user> -d <db> -f trading_app_init.sql
--
-- Notes:
-- - Creates schema: trading
-- - Creates tables: app_user, market_symbol, universe, universe_member, timeframe,
--   ohlcv_bar, data_fetch_log, strategy, analysis_run, run_score, run_signal, run_report
-- - Creates view: v_run_top3
-- - Inserts default timeframes: 1D, 1H, 15m

BEGIN;

CREATE SCHEMA IF NOT EXISTS trading;

-- Extensions (optional but recommended)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gin;

-- Users (optional; keep for auditability)
CREATE TABLE IF NOT EXISTS trading.app_user (
  user_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email            text UNIQUE,
  display_name     text,
  role             text NOT NULL DEFAULT 'user', -- admin/user
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Symbols master
CREATE TABLE IF NOT EXISTS trading.market_symbol (
  symbol_id        bigserial PRIMARY KEY,
  symbol           text NOT NULL UNIQUE,         -- e.g. 'FPT'
  exchange         text NOT NULL DEFAULT 'HOSE', -- VN30 mostly HOSE
  name             text,
  is_active        boolean NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Universe master (VN30)
CREATE TABLE IF NOT EXISTS trading.universe (
  universe_id      bigserial PRIMARY KEY,
  code             text NOT NULL UNIQUE,         -- e.g. 'VN30'
  name             text NOT NULL,
  source           text,                         -- 'vnstock' | 'manual'
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Universe membership with effective dating
CREATE TABLE IF NOT EXISTS trading.universe_member (
  universe_id      bigint NOT NULL REFERENCES trading.universe(universe_id) ON DELETE CASCADE,
  symbol_id        bigint NOT NULL REFERENCES trading.market_symbol(symbol_id) ON DELETE RESTRICT,
  effective_from   date NOT NULL,
  effective_to     date, -- null = active
  PRIMARY KEY (universe_id, symbol_id, effective_from)
);

CREATE INDEX IF NOT EXISTS idx_universe_member_active
ON trading.universe_member (universe_id, effective_from, effective_to);

-- Timeframe catalog
CREATE TABLE IF NOT EXISTS trading.timeframe (
  timeframe_id     smallserial PRIMARY KEY,
  code             text NOT NULL UNIQUE,         -- '1D', '1H', '15m'
  bar_seconds      integer NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);

INSERT INTO trading.timeframe(code, bar_seconds)
VALUES ('1D', 86400), ('1H', 3600), ('15m', 900)
ON CONFLICT (code) DO NOTHING;

-- OHLCV cache
CREATE TABLE IF NOT EXISTS trading.ohlcv_bar (
  symbol_id        bigint NOT NULL REFERENCES trading.market_symbol(symbol_id) ON DELETE CASCADE,
  timeframe_id     smallint NOT NULL REFERENCES trading.timeframe(timeframe_id) ON DELETE RESTRICT,
  ts              timestamptz NOT NULL,          -- bar start time
  open            numeric(18,4),
  high            numeric(18,4),
  low             numeric(18,4),
  close           numeric(18,4),
  volume          numeric(24,4),
  source          text NOT NULL DEFAULT 'vnstock',
  ingested_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (symbol_id, timeframe_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_ts
ON trading.ohlcv_bar (timeframe_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_ts
ON trading.ohlcv_bar (symbol_id, timeframe_id, ts DESC);

-- Fetch logs
CREATE TABLE IF NOT EXISTS trading.data_fetch_log (
  fetch_id         bigserial PRIMARY KEY,
  symbol_id        bigint REFERENCES trading.market_symbol(symbol_id),
  timeframe_id     smallint REFERENCES trading.timeframe(timeframe_id),
  requested_from   timestamptz,
  requested_to     timestamptz,
  rows_received    integer,
  cache_hit        boolean NOT NULL DEFAULT false,
  status           text NOT NULL,                -- 'ok' | 'error'
  error_message    text,
  duration_ms      integer,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fetchlog_created
ON trading.data_fetch_log (created_at DESC);

-- Strategy versioning
CREATE TABLE IF NOT EXISTS trading.strategy (
  strategy_id      bigserial PRIMARY KEY,
  code             text NOT NULL UNIQUE,         -- e.g. 'shortterm_v1'
  name             text NOT NULL,
  description      text,
  weights          jsonb NOT NULL,               -- e.g. {"trend":0.22,...}
  parameters       jsonb NOT NULL,               -- e.g. {"ema_fast":20,...}
  created_at       timestamptz NOT NULL DEFAULT now(),
  is_active        boolean NOT NULL DEFAULT true
);

-- Analysis runs
CREATE TABLE IF NOT EXISTS trading.analysis_run (
  run_id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  universe_id      bigint NOT NULL REFERENCES trading.universe(universe_id),
  timeframe_id     smallint NOT NULL REFERENCES trading.timeframe(timeframe_id),
  strategy_id      bigint NOT NULL REFERENCES trading.strategy(strategy_id),
  as_of            timestamptz NOT NULL,         -- data cutoff
  requested_by     uuid REFERENCES trading.app_user(user_id),
  status           text NOT NULL DEFAULT 'running', -- running|success|failed
  error_message    text,
  started_at       timestamptz NOT NULL DEFAULT now(),
  finished_at      timestamptz
);

CREATE INDEX IF NOT EXISTS idx_run_asof
ON trading.analysis_run (as_of DESC);

-- Scores per run & symbol
CREATE TABLE IF NOT EXISTS trading.run_score (
  run_id           uuid NOT NULL REFERENCES trading.analysis_run(run_id) ON DELETE CASCADE,
  symbol_id        bigint NOT NULL REFERENCES trading.market_symbol(symbol_id) ON DELETE RESTRICT,
  score_total      numeric(6,2) NOT NULL,        -- 0..100
  score_trend      numeric(6,2),
  score_base       numeric(6,2),
  score_breakout   numeric(6,2),
  score_volume     numeric(6,2),
  score_momentum   numeric(6,2),
  score_risk       numeric(6,2),
  penalties        jsonb,                        -- e.g. [{"type":"overextended","value":-5}]
  features         jsonb,                        -- raw computed features
  computed_at      timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, symbol_id)
);

CREATE INDEX IF NOT EXISTS idx_run_score_rank
ON trading.run_score (run_id, score_total DESC);

-- Trade signal suggestions
CREATE TABLE IF NOT EXISTS trading.run_signal (
  run_id           uuid NOT NULL REFERENCES trading.analysis_run(run_id) ON DELETE CASCADE,
  symbol_id        bigint NOT NULL REFERENCES trading.market_symbol(symbol_id) ON DELETE RESTRICT,
  entry_zone       jsonb NOT NULL,               -- {"from":..., "to":...}
  stop_loss        numeric(18,4),
  take_profit_1    numeric(18,4),
  take_profit_2    numeric(18,4),
  invalidation     jsonb,                        -- {"type":"swing_low","level":...}
  key_reasons      jsonb,                        -- ["reason1", ...]
  risk_notes       jsonb,                        -- ["note1", ...]
  created_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (run_id, symbol_id)
);

-- Snapshot report for fast API responses
CREATE TABLE IF NOT EXISTS trading.run_report (
  run_id           uuid PRIMARY KEY REFERENCES trading.analysis_run(run_id) ON DELETE CASCADE,
  top3             jsonb NOT NULL,
  ranking          jsonb NOT NULL,
  summary          jsonb,
  created_at       timestamptz NOT NULL DEFAULT now()
);

-- Convenience view
CREATE OR REPLACE VIEW trading.v_run_top3 AS
SELECT
  rs.run_id,
  ar.as_of,
  tf.code AS timeframe,
  ms.symbol,
  rs.score_total,
  rs.score_trend, rs.score_base, rs.score_breakout, rs.score_volume, rs.score_momentum, rs.score_risk
FROM trading.run_score rs
JOIN trading.analysis_run ar ON ar.run_id = rs.run_id
JOIN trading.market_symbol ms ON ms.symbol_id = rs.symbol_id
JOIN trading.timeframe tf ON tf.timeframe_id = ar.timeframe_id;

COMMIT;
