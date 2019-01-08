
-- These PRAGMAs MUST be enabled for correctness.
PRAGMA foreign_keys = ON;
PRAGMA recursive_triggers = ON;

-- These PRAGMAs MAY be enabled for performance. 
PRAGMA journal_mode = WAL; 
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA automatic_index = OFF;

