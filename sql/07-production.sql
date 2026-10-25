-- ============================================================
-- PRODUCTION — 7 tables
-- ============================================================

CREATE TABLE IF NOT EXISTS indent (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    indent_no           TEXT NOT NULL UNIQUE,
    wos_id              INTEGER NOT NULL REFERENCES wos(id),
    department_id       INTEGER REFERENCES department(id),
    requestor_name      TEXT NOT NULL,
    requestor_email     TEXT,
    indent_date         TEXT NOT NULL,
    date_needed_by      TEXT,
    approval_status     TEXT NOT NULL DEFAULT 'pending'
                        CHECK (approval_status IN ('pending','approved','rejected','partially_approved')),
    approved_by         INTEGER REFERENCES app_user(id),
    approved_date       TEXT,
    rejection_reason    TEXT,
    remarks             TEXT,
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by         INTEGER REFERENCES app_user(id),
    modified_at         TEXT,
    cancelled_by        INTEGER REFERENCES app_user(id),
    cancelled_at        TEXT,
    cancel_reason       TEXT
);

CREATE TABLE IF NOT EXISTS indent_line (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    indent_id       INTEGER NOT NULL REFERENCES indent(id) ON DELETE CASCADE,
    line_no         INTEGER NOT NULL,
    material_id     INTEGER NOT NULL REFERENCES material(id),
    warehouse_id    INTEGER REFERENCES warehouse(id),
    uom_id          INTEGER NOT NULL REFERENCES uom(id),
    qty_requested   REAL NOT NULL,
    qty_approved    REAL,
    qty_rejected    REAL DEFAULT 0,
    remarks         TEXT,
    UNIQUE (indent_id, line_no)
);

CREATE TABLE IF NOT EXISTS material_issue (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_no            TEXT NOT NULL UNIQUE,
    indent_id           INTEGER NOT NULL REFERENCES indent(id),
    wos_id              INTEGER REFERENCES wos(id),
    issue_date          TEXT NOT NULL,
    issued_to           TEXT,
    issued_to_contact   TEXT,
    issued_by           INTEGER REFERENCES app_user(id),
    warehouse_id        INTEGER REFERENCES warehouse(id),
    remarks             TEXT,
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_by        INTEGER REFERENCES app_user(id),
    cancelled_at        TEXT,
    cancel_reason       TEXT
);

CREATE TABLE IF NOT EXISTS material_issue_line (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    material_issue_id   INTEGER NOT NULL REFERENCES material_issue(id) ON DELETE CASCADE,
    indent_line_id      INTEGER NOT NULL REFERENCES indent_line(id),
    line_no             INTEGER NOT NULL,
    material_id         INTEGER NOT NULL REFERENCES material(id),
    uom_id              INTEGER NOT NULL REFERENCES uom(id),
    qty_issued          REAL NOT NULL,
    unit_consumption    REAL,
    remarks             TEXT,
    UNIQUE (material_issue_id, line_no)
);

CREATE TABLE IF NOT EXISTS production_entry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    production_no       TEXT NOT NULL UNIQUE,
    wos_id              INTEGER NOT NULL REFERENCES wos(id),
    production_date     TEXT NOT NULL,
    location_id         INTEGER REFERENCES warehouse(id),
    machine_name        TEXT,
    producer            TEXT,
    producer_mobile     TEXT,
    qty_produced        REAL NOT NULL,
    wastage_qty         REAL DEFAULT 0,
    remarks             TEXT,
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_by        INTEGER REFERENCES app_user(id),
    cancelled_at        TEXT,
    cancel_reason       TEXT
);

CREATE TABLE IF NOT EXISTS packing_entry (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    packing_no          TEXT NOT NULL UNIQUE,
    wos_id              INTEGER NOT NULL REFERENCES wos(id),
    packing_date        TEXT NOT NULL,
    location_id         INTEGER REFERENCES warehouse(id),
    qty_packed          REAL NOT NULL,
    master_cases        INTEGER,
    packed_by           TEXT,
    remarks             TEXT,
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_by        INTEGER REFERENCES app_user(id),
    cancelled_at        TEXT,
    cancel_reason       TEXT
);

CREATE TABLE IF NOT EXISTS dispatch_entry (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    dispatch_no             TEXT NOT NULL UNIQUE,
    wos_id                  INTEGER NOT NULL REFERENCES wos(id),
    dispatch_date           TEXT NOT NULL,
    qty_dispatched          REAL NOT NULL,
    master_cases            INTEGER,
    dispatch_status         TEXT DEFAULT 'dispatched'
                            CHECK (dispatch_status IN ('pending','partial','dispatched','delivered')),
    vehicle_no              TEXT,
    transporter_name        TEXT,
    lr_no                   TEXT,
    driver_name             TEXT,
    driver_mobile           TEXT,
    expected_delivery_date  TEXT,
    remarks                 TEXT,
    docstatus               INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by              INTEGER REFERENCES app_user(id),
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_by            INTEGER REFERENCES app_user(id),
    cancelled_at            TEXT,
    cancel_reason           TEXT
);

CREATE INDEX IF NOT EXISTS idx_indent_wos       ON indent(wos_id);
CREATE INDEX IF NOT EXISTS idx_indl_indent      ON indent_line(indent_id);
CREATE INDEX IF NOT EXISTS idx_mi_indent        ON material_issue(indent_id);
CREATE INDEX IF NOT EXISTS idx_mil_issue        ON material_issue_line(material_issue_id);
CREATE INDEX IF NOT EXISTS idx_mil_indent_line  ON material_issue_line(indent_line_id);
CREATE INDEX IF NOT EXISTS idx_pe_wos           ON production_entry(wos_id);
CREATE INDEX IF NOT EXISTS idx_pck_wos          ON packing_entry(wos_id);
CREATE INDEX IF NOT EXISTS idx_dsp_wos          ON dispatch_entry(wos_id);
