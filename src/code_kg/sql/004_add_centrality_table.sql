CREATE TABLE IF NOT EXISTS centrality_scores (
    node_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    score REAL NOT NULL,
    rank INTEGER,
    computed_at TEXT NOT NULL,
    params_json TEXT NOT NULL,
    PRIMARY KEY (node_id, metric)
);

CREATE INDEX IF NOT EXISTS idx_centrality_metric_rank
    ON centrality_scores(metric, rank);
