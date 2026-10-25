-- ============================================================
-- FINANCE — invoices + payments (6 tables)
-- ============================================================

CREATE TABLE IF NOT EXISTS sales_invoice (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no      TEXT NOT NULL UNIQUE,
    customer_id     INTEGER NOT NULL REFERENCES customer(id),
    customer_po_id  INTEGER REFERENCES customer_po(id),
    dispatch_id     INTEGER REFERENCES dispatch_entry(id),
    invoice_date    TEXT NOT NULL,
    due_date        TEXT,
    subtotal        REAL NOT NULL DEFAULT 0,
    tax_rate        REAL NOT NULL DEFAULT 18,
    tax_amount      REAL NOT NULL DEFAULT 0,
    total_amount    REAL NOT NULL,
    status          TEXT DEFAULT 'sent'
                    CHECK (status IN ('draft','sent','partially_paid','paid','overdue','cancelled')),
    docstatus       INTEGER NOT NULL DEFAULT 1 CHECK (docstatus IN (0,1,2)),
    remarks         TEXT,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales_invoice_line (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_invoice_id    INTEGER NOT NULL REFERENCES sales_invoice(id) ON DELETE CASCADE,
    line_no             INTEGER NOT NULL,
    sku_id              INTEGER REFERENCES sku(id),
    wos_id              INTEGER REFERENCES wos(id),
    description         TEXT,
    qty                 REAL NOT NULL,
    rate                REAL NOT NULL,
    amount              REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS purchase_invoice (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no            TEXT NOT NULL UNIQUE,
    supplier_invoice_no   TEXT,
    supplier_id           INTEGER NOT NULL REFERENCES supplier(id),
    supplier_po_id        INTEGER REFERENCES supplier_po(id),
    grn_id                INTEGER REFERENCES grn(id),
    invoice_date          TEXT NOT NULL,
    due_date              TEXT,
    subtotal              REAL NOT NULL DEFAULT 0,
    tax_rate              REAL NOT NULL DEFAULT 18,
    tax_amount            REAL NOT NULL DEFAULT 0,
    total_amount          REAL NOT NULL,
    status                TEXT DEFAULT 'unpaid'
                          CHECK (status IN ('draft','unpaid','partially_paid','paid','cancelled')),
    docstatus             INTEGER NOT NULL DEFAULT 1 CHECK (docstatus IN (0,1,2)),
    remarks               TEXT,
    created_at            TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS purchase_invoice_line (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    purchase_invoice_id     INTEGER NOT NULL REFERENCES purchase_invoice(id) ON DELETE CASCADE,
    line_no                 INTEGER NOT NULL,
    material_id             INTEGER REFERENCES material(id),
    grn_line_id             INTEGER REFERENCES grn_line(id),
    description             TEXT,
    qty                     REAL NOT NULL,
    rate                    REAL NOT NULL,
    amount                  REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_entry (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_no      TEXT NOT NULL UNIQUE,
    payment_type    TEXT NOT NULL CHECK (payment_type IN ('receipt','payment')),
    party_type      TEXT NOT NULL CHECK (party_type IN ('customer','supplier')),
    party_id        INTEGER NOT NULL,
    payment_date    TEXT NOT NULL,
    amount          REAL NOT NULL,
    payment_mode    TEXT CHECK (payment_mode IN ('cash','bank','upi','cheque','neft','rtgs')),
    reference_no    TEXT,
    remarks         TEXT,
    docstatus       INTEGER NOT NULL DEFAULT 1 CHECK (docstatus IN (0,1,2)),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payment_allocation (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_entry_id    INTEGER NOT NULL REFERENCES payment_entry(id) ON DELETE CASCADE,
    invoice_type        TEXT NOT NULL CHECK (invoice_type IN ('sales_invoice','purchase_invoice')),
    invoice_id          INTEGER NOT NULL,
    allocated_amount    REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_si_customer  ON sales_invoice(customer_id);
CREATE INDEX IF NOT EXISTS idx_pi_supplier  ON purchase_invoice(supplier_id);
CREATE INDEX IF NOT EXISTS idx_pay_party    ON payment_entry(party_type, party_id);
CREATE INDEX IF NOT EXISTS idx_pay_alloc    ON payment_allocation(invoice_type, invoice_id);
