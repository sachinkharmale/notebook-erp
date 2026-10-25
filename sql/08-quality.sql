-- ============================================================
-- QUALITY — polymorphic QC record
-- ============================================================

CREATE TABLE IF NOT EXISTS qc_record (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    qc_no           TEXT NOT NULL UNIQUE,
    ref_type        TEXT NOT NULL CHECK (ref_type IN ('grn','production','dispatch','wos')),
    ref_id          INTEGER NOT NULL,
    qc_date         TEXT NOT NULL,
    qc_stage        TEXT CHECK (qc_stage IN ('incoming','in_process','final','pre_dispatch')),
    result          TEXT NOT NULL CHECK (result IN ('pass','fail','hold','pending')),
    inspector_name  TEXT,
    fail_reason     TEXT,
    remarks         TEXT,
    created_by      INTEGER REFERENCES app_user(id),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qc_ref ON qc_record(ref_type, ref_id);
