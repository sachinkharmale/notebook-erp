-- ============================================================
-- GATE — vehicle + visitor logs (2 tables)
-- ============================================================

CREATE TABLE IF NOT EXISTS vehicle_visit (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_no            TEXT NOT NULL UNIQUE,
    visit_date          TEXT NOT NULL,
    load_type           TEXT NOT NULL CHECK (load_type IN ('inward','outward','both','internal')),
    vehicle_number      TEXT NOT NULL,
    vehicle_code        TEXT,
    driver_name         TEXT,
    driver_licence      TEXT,
    driver_mobile       TEXT,
    party_name          TEXT,
    supplier_id         INTEGER REFERENCES supplier(id),
    customer_id         INTEGER REFERENCES customer(id),
    item_reference      TEXT,
    inward_challan_no   TEXT,
    outward_challan_no  TEXT,
    container_no        TEXT,
    container_seal_no   TEXT,
    rfid_seal_no        TEXT,
    in_time             TEXT,
    first_weight        REAL,
    last_weight         REAL,
    out_time            TEXT,
    weighbridge_station TEXT,
    weight_unit         TEXT DEFAULT 'kg',
    remarks             TEXT,
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at         TEXT
);

CREATE TABLE IF NOT EXISTS visitor_visit (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_no            TEXT NOT NULL UNIQUE,
    in_time             TEXT NOT NULL,
    out_time            TEXT,
    out_verified_by     INTEGER REFERENCES app_user(id),
    company_name        TEXT,
    visitor_name        TEXT NOT NULL,
    coming_from         TEXT,
    mobile              TEXT,
    whom_to_meet        TEXT,
    host_department_id  INTEGER REFERENCES department(id),
    purpose             TEXT,
    items_carried       TEXT,
    id_proof_type       TEXT,
    id_proof_number     TEXT,
    vehicle_number      TEXT,
    vehicle_type        TEXT,
    badge_no            TEXT,
    remarks             TEXT,
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at         TEXT
);

CREATE INDEX IF NOT EXISTS idx_vv_date    ON vehicle_visit(visit_date);
CREATE INDEX IF NOT EXISTS idx_vv_vehicle ON vehicle_visit(vehicle_number);
CREATE INDEX IF NOT EXISTS idx_vis_in     ON visitor_visit(in_time);
