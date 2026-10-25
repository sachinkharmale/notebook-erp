-- ============================================================
-- CROSS-CUTTING — attachments, audit, naming, permissions
-- ============================================================

CREATE TABLE IF NOT EXISTS attachments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_doctype     TEXT NOT NULL,
    ref_id          INTEGER NOT NULL,
    doc_type        TEXT NOT NULL CHECK (doc_type IN
                    ('challan','invoice','qc_certificate','po_pdf',
                     'dispatch_doc','vehicle_slip','other')),
    file_name       TEXT NOT NULL,
    file_url        TEXT NOT NULL,
    file_size       INTEGER,
    mime_type       TEXT,
    uploaded_by     INTEGER REFERENCES app_user(id),
    uploaded_at     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name      TEXT NOT NULL,
    record_id       INTEGER NOT NULL,
    action          TEXT NOT NULL CHECK (action IN
                    ('create','update','submit','cancel','amend','delete')),
    field_name      TEXT,
    old_value       TEXT,
    new_value       TEXT,
    changed_by      INTEGER REFERENCES app_user(id),
    changed_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS naming_series (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    entity          TEXT NOT NULL,
    prefix          TEXT NOT NULL,
    next_no         INTEGER NOT NULL DEFAULT 1,
    reset_period    TEXT CHECK (reset_period IN ('never','yearly','monthly')),
    last_reset      TEXT,
    UNIQUE (entity, prefix)
);

CREATE TABLE IF NOT EXISTS role_permission (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    role            TEXT NOT NULL,
    doctype         TEXT NOT NULL,
    can_read        INTEGER NOT NULL DEFAULT 0 CHECK (can_read IN (0,1)),
    can_create      INTEGER NOT NULL DEFAULT 0 CHECK (can_create IN (0,1)),
    can_edit        INTEGER NOT NULL DEFAULT 0 CHECK (can_edit IN (0,1)),
    can_submit      INTEGER NOT NULL DEFAULT 0 CHECK (can_submit IN (0,1)),
    can_cancel      INTEGER NOT NULL DEFAULT 0 CHECK (can_cancel IN (0,1)),
    UNIQUE (role, doctype)
);

CREATE INDEX IF NOT EXISTS idx_att_ref   ON attachments(ref_doctype, ref_id);
CREATE INDEX IF NOT EXISTS idx_audit_rec ON audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_rp_role   ON role_permission(role);
