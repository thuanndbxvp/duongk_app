CREATE TABLE quota_ledger (
  id BIGSERIAL PRIMARY KEY,
  api_key_id TEXT NOT NULL,
  date DATE NOT NULL,
  units_used INT NOT NULL DEFAULT 0,
  units_limit INT NOT NULL DEFAULT 10000,
  UNIQUE(api_key_id, date)
);