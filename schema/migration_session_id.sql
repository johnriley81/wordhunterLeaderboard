-- Session-scoped leaderboard UPSERT (Option A): one row per (puzzle, session_id), best score wins.
-- session_id is nullable for legacy rows submitted before this migration.

ALTER TABLE leaderboard ADD COLUMN session_id VARCHAR(36) NULL;
CREATE UNIQUE INDEX idx_leaderboard_puzzle_session ON leaderboard (puzzle, session_id);
DROP INDEX uq_leaderboard_puzzle_player_score_trophy;
