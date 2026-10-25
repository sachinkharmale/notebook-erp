-- ============================================================
-- MASTERS — 10 tables
-- SQLite schema (Phase 1)
-- ============================================================

PRAGMA foreign_keys = ON;

-- 1. UOM
CREATE TABLE IF NOT EXISTS uom (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Warehouse
CREATE TABLE IF NOT EXISTS warehouse (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    location            TEXT,
    is_consumable_store INTEGER NOT NULL DEFAULT 0 CHECK (is_consumable_store IN (0,1)),
    active              INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Customer
CREATE TABLE IF NOT EXISTS customer (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    address         TEXT,
    gstin           TEXT,
    contact_person  TEXT,
    mobile          TEXT,
    email           TEXT,
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at     TEXT
);

-- 4. Supplier
CREATE TABLE IF NOT EXISTS supplier (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    address         TEXT,
    gstin           TEXT,
    contact_person  TEXT,
    mobile          TEXT,
    email           TEXT,
    payment_terms   TEXT,
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at     TEXT
);

-- 5. Department
CREATE TABLE IF NOT EXISTS department (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    code    TEXT NOT NULL UNIQUE,
    name    TEXT NOT NULL,
    active  INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

-- 6. App User
CREATE TABLE IF NOT EXISTS app_user (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    email           TEXT,
    mobile          TEXT,
    department_id   INTEGER REFERENCES department(id),
    role            TEXT NOT NULL CHECK (role IN
        ('admin','sales','planner','store','production','qc','dispatch','gate','finance','viewer')),
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Vehicle
CREATE TABLE IF NOT EXISTS vehicle (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    number        TEXT NOT NULL UNIQUE,
    vehicle_type  TEXT,
    vehicle_code  TEXT,
    active        INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

-- 8. SKU (Finished Goods)
CREATE TABLE IF NOT EXISTS sku (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    category        TEXT,
    product_group   TEXT,
    uom_id          INTEGER NOT NULL REFERENCES uom(id),
    book_type       TEXT CHECK (book_type IN ('notebook','textbook','register','diary','other')),
    spec_pages      INTEGER,
    spec_design     TEXT,
    spec_size       TEXT,
    spec_ruling     TEXT,
    spec_binding    TEXT,
    isbn            TEXT,
    subject         TEXT,
    grade           TEXT,
    edition         TEXT,
    author          TEXT,
    publisher       TEXT,
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Material (Raw Material + Consumable)
CREATE TABLE IF NOT EXISTS material (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    code                TEXT NOT NULL UNIQUE,
    name                TEXT NOT NULL,
    spec_signature      TEXT NOT NULL UNIQUE,
    category            TEXT NOT NULL DEFAULT 'raw_material'
                        CHECK (category IN ('raw_material','consumable')),
    material_group      TEXT NOT NULL,
    uom_id              INTEGER NOT NULL REFERENCES uom(id),
    physical_form       TEXT NOT NULL
                        CHECK (physical_form IN
                        ('sheet','roll','reel','carton','board','wire','liquid','piece','plate')),
    width_cm            REAL,
    length_cm           REAL,
    height_cm           REAL,
    gsm                 REAL,
    thickness_mm        REAL,
    ply                 INTEGER,
    paper_type          TEXT,
    ink_color           TEXT,
    ink_type            TEXT,
    plate_size          TEXT,
    fsc_status          TEXT CHECK (fsc_status IN ('FSC','NON_FSC')),
    is_inner_page       INTEGER DEFAULT 0 CHECK (is_inner_page IN (0,1)),
    is_cover_material   INTEGER DEFAULT 0 CHECK (is_cover_material IN (0,1)),
    sheets_per_kg       REAL,
    kg_per_sheet        REAL,
    reorder_level       REAL,
    lead_time_days      INTEGER,
    active              INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at         TEXT
);

CREATE INDEX IF NOT EXISTS idx_material_category ON material(category);
CREATE INDEX IF NOT EXISTS idx_material_group    ON material(material_group);

-- 10. Cost Center
CREATE TABLE IF NOT EXISTS cost_center (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    category    TEXT CHECK (category IN ('production','service','sales','admin','other')),
    is_active   INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
