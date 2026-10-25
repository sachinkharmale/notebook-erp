-- ============================================================
-- ENGINEERING — 4 tables: bom_template, bom_template_line,
--                          wos_bom, wos_bom_line
-- ============================================================

CREATE TABLE IF NOT EXISTS bom_template (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_id              TEXT NOT NULL UNIQUE,
    bom_group_id        TEXT,
    product_category    TEXT,
    product_group_name  TEXT,
    size                TEXT,
    pages               INTEGER,
    ruling_type         TEXT,
    binding_type        TEXT,
    active              INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    docstatus           INTEGER NOT NULL DEFAULT 0 CHECK (docstatus IN (0,1,2)),
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_by         INTEGER REFERENCES app_user(id),
    modified_at         TEXT
);

CREATE TABLE IF NOT EXISTS bom_template_line (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_template_id         INTEGER NOT NULL REFERENCES bom_template(id) ON DELETE CASCADE,
    line_no                 INTEGER NOT NULL,
    line_type               TEXT NOT NULL DEFAULT 'raw_material'
                            CHECK (line_type IN ('raw_material','consumable')),
    spec_material_group     TEXT NOT NULL,
    spec_physical_form      TEXT NOT NULL
                            CHECK (spec_physical_form IN
                            ('sheet','roll','reel','carton','board','wire','liquid','piece','plate')),
    spec_width_cm           REAL,
    spec_length_cm          REAL,
    spec_height_cm          REAL,
    spec_gsm                REAL,
    spec_thickness_mm       REAL,
    spec_ply                INTEGER,
    spec_paper_type         TEXT,
    spec_ink_color          TEXT,
    spec_ink_type           TEXT,
    spec_plate_size         TEXT,
    spec_signature          TEXT NOT NULL,
    material_id             INTEGER REFERENCES material(id),
    uom_id                  INTEGER NOT NULL REFERENCES uom(id),
    base_qty_per_1000       REAL NOT NULL,
    wastage_pct             REAL DEFAULT 0,
    loss_pct                REAL DEFAULT 0,
    effective_qty_per_1000  REAL NOT NULL,
    process_stage           TEXT,
    applies_to              TEXT,
    mandatory               INTEGER NOT NULL DEFAULT 1 CHECK (mandatory IN (0,1)),
    active                  INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    remarks                 TEXT,
    created_at              TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bom_template_id, line_no)
);

CREATE TABLE IF NOT EXISTS wos_bom (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    wos_id              INTEGER NOT NULL UNIQUE REFERENCES wos(id) ON DELETE CASCADE,
    bom_template_id     INTEGER NOT NULL REFERENCES bom_template(id),
    matched_on_snapshot TEXT,
    created_by          INTEGER REFERENCES app_user(id),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wos_bom_line (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    wos_bom_id              INTEGER NOT NULL REFERENCES wos_bom(id) ON DELETE CASCADE,
    material_id             INTEGER NOT NULL REFERENCES material(id),
    uom_id                  INTEGER NOT NULL REFERENCES uom(id),
    base_qty_per_1000       REAL NOT NULL,
    wastage_pct             REAL DEFAULT 0,
    loss_pct                REAL DEFAULT 0,
    effective_qty_per_1000  REAL NOT NULL,
    order_qty_basis         REAL NOT NULL,
    required_qty            REAL NOT NULL,
    spec_signature          TEXT,
    remarks                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_btl_template  ON bom_template_line(bom_template_id);
CREATE INDEX IF NOT EXISTS idx_btl_material  ON bom_template_line(material_id);
CREATE INDEX IF NOT EXISTS idx_wbl_wos_bom   ON wos_bom_line(wos_bom_id);
CREATE INDEX IF NOT EXISTS idx_wbl_material  ON wos_bom_line(material_id);
