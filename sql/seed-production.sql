-- ============================================================
-- SEED: full production chain on WOS-2526-00001
-- Order qty = 40000. We will:
--   Indent 20520 kg paper + 34.4 LTR ink (BOM requirement)
--   Approve both lines
--   Issue 20000 kg paper (partial — all we have in stock)
--   Produce 15000, Pack 15000, Dispatch 8000 (partial)
-- ============================================================

-- 1. Indent header (draft)
INSERT OR IGNORE INTO indent
(indent_no, wos_id, department_id, requestor_name, indent_date,
 approval_status, docstatus, created_by)
SELECT 'IND-2526-00001', w.id, d.id, 'Production Supervisor', DATE('now'),
       'pending', 0, u.id
FROM wos w, department d, app_user u
WHERE w.wos_no='WOS-2526-00001' AND d.code='PROD' AND u.username='admin';

-- 2. Indent line 1: inner paper (20520 kg = 513 * 40)
INSERT OR IGNORE INTO indent_line
(indent_id, line_no, material_id, warehouse_id, uom_id,
 qty_requested, qty_approved)
SELECT i.id, 1, m.id, w.id, 1, 20520, 20520
FROM indent i, material m, warehouse w
WHERE i.indent_no='IND-2526-00001' AND m.code='PAP-080-70-100' AND w.code='WH-RM-01';

-- 3. Indent line 2: ink (34.4 LTR = 0.86 * 40)
INSERT OR IGNORE INTO indent_line
(indent_id, line_no, material_id, warehouse_id, uom_id,
 qty_requested, qty_approved)
SELECT i.id, 2, m.id, w.id, 5, 34.4, 34.4
FROM indent i, material m, warehouse w
WHERE i.indent_no='IND-2526-00001' AND m.code='INK-BLACK-OFFSET' AND w.code='WH-RM-01';

-- 4. Approve indent
UPDATE indent
SET approval_status='approved',
    approved_by=(SELECT id FROM app_user WHERE username='admin'),
    approved_date=CURRENT_TIMESTAMP,
    docstatus=1
WHERE indent_no='IND-2526-00001' AND docstatus=0;

-- 5. Material Issue header (draft)
INSERT OR IGNORE INTO material_issue
(issue_no, indent_id, wos_id, issue_date, issued_to, issued_by, warehouse_id,
 docstatus, created_by)
SELECT 'ISS-2526-00001', i.id, i.wos_id, DATE('now'), 'Production Line 1',
       u.id, w.id, 0, u.id
FROM indent i, warehouse w, app_user u
WHERE i.indent_no='IND-2526-00001' AND w.code='WH-RM-01' AND u.username='admin';

-- 6. Issue line 1: paper 20000 kg (all in stock)
INSERT OR IGNORE INTO material_issue_line
(material_issue_id, indent_line_id, line_no, material_id, uom_id, qty_issued)
SELECT mi.id, il.id, 1, m.id, 1, 20000
FROM material_issue mi
JOIN indent i ON i.id = mi.indent_id AND i.indent_no='IND-2526-00001'
JOIN indent_line il ON il.indent_id = i.id AND il.line_no = 1
CROSS JOIN material m
WHERE m.code='PAP-080-70-100';

-- 7. Submit Material Issue → R10 fires → stock out -20000
UPDATE material_issue
SET docstatus=1
WHERE issue_no='ISS-2526-00001' AND docstatus=0;

-- 8. Production Entry (submitted) → R4 checks material issued ✓
INSERT OR IGNORE INTO production_entry
(production_no, wos_id, production_date, location_id, machine_name, producer,
 qty_produced, wastage_qty, docstatus, created_by)
SELECT 'PRD-2526-00001', w.id, DATE('now'), wloc.id, 'Press-01', 'Operator A',
       15000, 200, 1, u.id
FROM wos w, warehouse wloc, app_user u
WHERE w.wos_no='WOS-2526-00001' AND wloc.code='WH-FG-01' AND u.username='admin';

-- 9. Packing Entry (submitted) → R3 checks packed <= produced ✓
INSERT OR IGNORE INTO packing_entry
(packing_no, wos_id, packing_date, location_id, qty_packed, master_cases,
 packed_by, docstatus, created_by)
SELECT 'PCK-2526-00001', w.id, DATE('now'), wloc.id, 15000, 750,
        'Packing Team 1', 1, u.id
FROM wos w, warehouse wloc, app_user u
WHERE w.wos_no='WOS-2526-00001' AND wloc.code='WH-FG-01' AND u.username='admin';

-- 10. Dispatch Entry (submitted, partial) → R2 checks dispatched <= packed ✓
INSERT OR IGNORE INTO dispatch_entry
(dispatch_no, wos_id, dispatch_date, qty_dispatched, master_cases,
 dispatch_status, vehicle_no, transporter_name, lr_no, driver_name,
 docstatus, created_by)
SELECT 'DSP-2526-00001', w.id, DATE('now'), 8000, 400,
        'partial', 'MH-12-CD-5678', 'BlueDart Logistics', 'LR-789',
        'Ramesh', 1, u.id
FROM wos w, app_user u
WHERE w.wos_no='WOS-2526-00001' AND u.username='admin';

-- 11. QC record (final, pass, linked to production)
INSERT OR IGNORE INTO qc_record
(qc_no, ref_type, ref_id, qc_date, qc_stage, result, inspector_name,
 created_by)
SELECT 'QC-2526-00001', 'production', pe.id, DATE('now'), 'final', 'pass',
       'Inspector Raj', u.id
FROM production_entry pe, app_user u
WHERE pe.production_no='PRD-2526-00001' AND u.username='admin';
