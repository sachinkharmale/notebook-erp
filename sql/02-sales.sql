-- ============================================================
-- SALES — 3 tables: customer_po, customer_po_line, wos
-- ============================================================

CREATE TABLE IF NOT EXISTS customer_po (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    po_no           TEXT NOT NULL UNIQUE,
    customer_id     INTEGER NOT NULL REFERENCES customer(id),
    po_date         TEXT NOT NULL,
    customer_ref    TEXT,
    currency        TEXT DEFAULT 'INR',
    status          TEXT NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','confirmed','in_execution','completed','cancelled')),
    remarks         TEXT,
    docstatus       INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by      INTEGER REFERENCES app_user(id),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by     INTEGER REFERENCES app_user(id),
    modified_at     TEXT,
    cancelled_by    INTEGER REFERENCES app_user(id),
    cancelled_at    TEXT,
    cancel_reason   TEXT
);

CREATE TABLE IF NOT EXISTS customer_po_line (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_po_id  INTEGER NOT NULL REFERENCES customer_po(id) ON DELETE CASCADE,
    line_no         INTEGER NOT NULL,
    sku_id          INTEGER NOT NULL REFERENCES sku(id),
    qty             REAL NOT NULL,
    rate            REAL,
    delivery_date   TEXT,
    remarks         TEXT,
    UNIQUE (customer_po_id, line_no)
);

CREATE TABLE IF NOT EXISTS wos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    wos_no              TEXT NOT NULL UNIQUE,
    po_line_id          INTEGER NOT NULL REFERENCES customer_po_line(id),
    customer_id         INTEGER NOT NULL REFERENCES customer(id),
    sku_id              INTEGER NOT NULL REFERENCES sku(id),
    order_qty           REAL NOT NULL,
    master_case_pack    INTEGER,
    inner_case_pack     INTEGER,
    ship_date           TEXT,
    merchandiser        TEXT,
    testing_sample_pickup TEXT,
    location_id         INTEGER REFERENCES warehouse(id),
    remark              TEXT,
    wos_status          TEXT NOT NULL DEFAULT 'pending_shipment'
                        CHECK (wos_status IN ('pending_shipment','bom_created','material_procured',
                               'in_production','packed','ready_to_ship','partially_dispatched',
                               'dispatched','closed','on_hold','cancelled')),
    locked              INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0,1)),
    docstatus           INTEGER NOT NULL DEFAULT 1 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by         INTEGER REFERENCES app_user(id),
    modified_at         TEXT,
    cancelled_by        INTEGER REFERENCES app_user(id),
    cancelled_at        TEXT,
    cancel_reason       TEXT
);

CREATE INDEX IF NOT EXISTS idx_cpl_po         ON customer_po_line(customer_po_id);
CREATE INDEX IF NOT EXISTS idx_wos_po_line    ON wos(po_line_id);
CREATE INDEX IF NOT EXISTS idx_wos_customer   ON wos(customer_id);
CREATE INDEX IF NOT EXISTS idx_wos_status     ON wos(wos_status);
CREATE INDEX IF NOT EXISTS idx_wos_ship_date  ON wos(ship_date);
