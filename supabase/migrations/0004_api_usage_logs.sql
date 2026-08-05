CREATE TABLE api_usage_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  job_id UUID REFERENCES jobs(id),
  provider TEXT NOT NULL,
  operation TEXT NOT NULL,
  input_tokens INT,
  output_tokens INT,
  cost_usd NUMERIC(10,6),
  quota_units INT,
  api_key_id TEXT,
  status_code INT,
  duration_ms INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_api_usage_provider_date ON api_usage_logs(provider, created_at DESC);