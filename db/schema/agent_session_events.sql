CREATE TABLE IF NOT EXISTS agent_session_events (
  run_id TEXT PRIMARY KEY,
  actor TEXT NOT NULL,
  repo TEXT NOT NULL,
  branch TEXT NOT NULL,
  workflow TEXT NOT NULL,
  prompt_hash TEXT NOT NULL,
  model TEXT NOT NULL,
  tool_calls TEXT NOT NULL,
  files_changed TEXT NOT NULL,
  tests_run TEXT NOT NULL,
  cost_estimate REAL NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,
  risk_flags TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_agent_session_events_repo_workflow
  ON agent_session_events (repo, workflow);

CREATE INDEX IF NOT EXISTS idx_agent_session_events_started_at
  ON agent_session_events (started_at);

CREATE INDEX IF NOT EXISTS idx_agent_session_events_status
  ON agent_session_events (status);
