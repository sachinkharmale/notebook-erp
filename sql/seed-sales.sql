-- ============================================================
-- SEED: sales data
-- ============================================================

-- Customers
INSERT OR IGNORE INTO customer (code, name, gstin, mobile) VALUES
('CUST-001','ABC Stationers','27AABCU9603R1ZM','9876543210'),
('CUST-002','XYZ Educational Supplies','07AABCU9603R1ZQ','9876543211');

-- Suppliers
INSERT OR IGNORE INTO supplier (code, name, gstin) VALUES
('SUP-001','Raj Paper Mills','27AABCU9603R1ZP'),
('SUP-002','Print Solutions Ltd','27AABCU9603R1ZR');

-- SKUs
INSERT OR IGNORE INTO sku (code, name, category, product_group, book_type, uom_id,
                           spec_pages, spec_size, spec_ruling, spec_binding) VALUES
('NB-A5-192-SL-SPIRAL','Notebook A5 192 pages Single Line Spiral',
 'Notebook','A5 Spiral','notebook',2,192,'A5','Single Line','Spiral'),
('NB-A4-200-RL-WIREO','Notebook A4 200 pages Ruled Wire-O',
 'Notebook','A4 Wire-O','notebook',2,200,'A4','Ruled','Wire-O');

-- Sample Customer PO
INSERT OR IGNORE INTO customer_po
(po_no, customer_id, po_date, status, docstatus, created_by)
SELECT 'CPO-2526-00001', c.id, DATE('now'), 'confirmed', 1, u.id
FROM customer c, app_user u
WHERE c.code='CUST-001' AND u.username='admin';

-- 2 lines on that PO
INSERT OR IGNORE INTO customer_po_line
(customer_po_id, line_no, sku_id, qty, rate, delivery_date)
SELECT cp.id, 1, s.id, 40000, 45.00, DATE('now', '+30 days')
FROM customer_po cp, sku s
WHERE cp.po_no='CPO-2526-00001' AND s.code='NB-A5-192-SL-SPIRAL';

INSERT OR IGNORE INTO customer_po_line
(customer_po_id, line_no, sku_id, qty, rate, delivery_date)
SELECT cp.id, 2, s.id, 25000, 65.00, DATE('now', '+45 days')
FROM customer_po cp, sku s
WHERE cp.po_no='CPO-2526-00001' AND s.code='NB-A4-200-RL-WIREO';

-- 2 WOS (one per PO line)
INSERT OR IGNORE INTO wos
(wos_no, po_line_id, customer_id, sku_id, order_qty, ship_date, wos_status, docstatus, created_by)
SELECT 'WOS-2526-00001', cpl.id, cp.customer_id, cpl.sku_id, cpl.qty, cpl.delivery_date,
       'pending_shipment', 1, u.id
FROM customer_po_line cpl
JOIN customer_po cp ON cp.id = cpl.customer_po_id
CROSS JOIN app_user u
WHERE cp.po_no='CPO-2526-00001' AND cpl.line_no = 1 AND u.username='admin';

INSERT OR IGNORE INTO wos
(wos_no, po_line_id, customer_id, sku_id, order_qty, ship_date, wos_status, docstatus, created_by)
SELECT 'WOS-2526-00002', cpl.id, cp.customer_id, cpl.sku_id, cpl.qty, cpl.delivery_date,
       'pending_shipment', 1, u.id
FROM customer_po_line cpl
JOIN customer_po cp ON cp.id = cpl.customer_po_id
CROSS JOIN app_user u
WHERE cp.po_no='CPO-2526-00001' AND cpl.line_no = 2 AND u.username='admin';
