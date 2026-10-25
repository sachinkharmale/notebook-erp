-- ============================================================
-- SEED: Sales Invoice (from dispatch) + Payment receipt + PO Invoice
-- ============================================================

-- 1. Sales Invoice from Dispatch (8000 qty @ 45.00, tax 18%)
INSERT OR IGNORE INTO sales_invoice
(invoice_no, customer_id, customer_po_id, dispatch_id, invoice_date,
 due_date, subtotal, tax_rate, tax_amount, total_amount, status, docstatus)
SELECT 'SI-2526-00001', w.customer_id, cp.id, de.id, DATE('now'),
       DATE('now', '+30 days'),
       de.qty_dispatched * cpl.rate,
       18,
       de.qty_dispatched * cpl.rate * 0.18,
       de.qty_dispatched * cpl.rate * 1.18,
       'sent', 1
FROM dispatch_entry de
JOIN wos w ON w.id = de.wos_id
JOIN customer_po_line cpl ON cpl.id = w.po_line_id
JOIN customer_po cp ON cp.id = cpl.customer_po_id
WHERE de.dispatch_no='DSP-2526-00001';

INSERT OR IGNORE INTO sales_invoice_line
(sales_invoice_id, line_no, sku_id, wos_id, description, qty, rate, amount)
SELECT si.id, 1, w.sku_id, w.id, s.name,
       de.qty_dispatched, cpl.rate,
       de.qty_dispatched * cpl.rate
FROM sales_invoice si
JOIN dispatch_entry de ON de.id = si.dispatch_id
JOIN wos w ON w.id = de.wos_id
JOIN customer_po_line cpl ON cpl.id = w.po_line_id
JOIN sku s ON s.id = w.sku_id
WHERE si.invoice_no='SI-2526-00001';

-- 2. Payment Receipt (partial: 200,000 against the invoice)
INSERT OR IGNORE INTO payment_entry
(payment_no, payment_type, party_type, party_id, payment_date, amount,
 payment_mode, reference_no, docstatus)
SELECT 'PAY-2526-00001', 'receipt', 'customer', si.customer_id, DATE('now'),
       200000, 'neft', 'NEFT-88012', 1
FROM sales_invoice si
WHERE si.invoice_no='SI-2526-00001';

INSERT OR IGNORE INTO payment_allocation
(payment_entry_id, invoice_type, invoice_id, allocated_amount)
SELECT pe.id, 'sales_invoice', si.id, 200000
FROM payment_entry pe, sales_invoice si
WHERE pe.payment_no='PAY-2526-00001' AND si.invoice_no='SI-2526-00001';

-- 3. Purchase Invoice from GRN (2 lines, tax 18%)
INSERT OR IGNORE INTO purchase_invoice
(invoice_no, supplier_invoice_no, supplier_id, supplier_po_id, grn_id,
 invoice_date, due_date, subtotal, tax_rate, tax_amount, total_amount,
 status, docstatus)
SELECT 'PI-2526-00001', 'INV-2526-0042', g.supplier_id, g.supplier_po_id, g.id,
       DATE('now'), DATE('now', '+30 days'),
       (SELECT COALESCE(SUM(gl.qty_received * gl.rate), 0) FROM grn_line gl WHERE gl.grn_id = g.id),
       18,
       (SELECT COALESCE(SUM(gl.qty_received * gl.rate), 0) FROM grn_line gl WHERE gl.grn_id = g.id) * 0.18,
       (SELECT COALESCE(SUM(gl.qty_received * gl.rate), 0) FROM grn_line gl WHERE gl.grn_id = g.id) * 1.18,
       'unpaid', 1
FROM grn g
WHERE g.grn_no='GRN-2526-00001';

INSERT OR IGNORE INTO purchase_invoice_line
(purchase_invoice_id, line_no, material_id, grn_line_id, description,
 qty, rate, amount)
SELECT pi.id, gl.line_no, gl.material_id, gl.id, m.name,
       gl.qty_received, gl.rate, gl.qty_received * gl.rate
FROM purchase_invoice pi
JOIN grn g ON g.id = pi.grn_id
JOIN grn_line gl ON gl.grn_id = g.id
JOIN material m ON m.id = gl.material_id
WHERE pi.invoice_no='PI-2526-00001';
