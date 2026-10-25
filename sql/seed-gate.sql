-- ============================================================
-- SEED: 1 vehicle visit + 1 visitor visit
-- ============================================================

INSERT OR IGNORE INTO vehicle_visit
(visit_no, visit_date, load_type, vehicle_number, driver_name, driver_mobile,
 party_name, supplier_id, inward_challan_no, in_time, first_weight,
 last_weight, out_time, weighbridge_station, docstatus, created_by)
SELECT 'VEH-2526-00001', DATE('now'), 'inward', 'MH-12-AB-1234',
       'Suresh Kumar', '9876500001', 'Raj Paper Mills', s.id,
       'INV-2526-0042', DATETIME('now', '-2 hours'),
       24500.50, 3900.50, DATETIME('now', '-90 minutes'),
       'WB-1', 1, u.id
FROM supplier s, app_user u
WHERE s.code='SUP-001' AND u.username='admin';

INSERT OR IGNORE INTO visitor_visit
(visit_no, in_time, out_time, company_name, visitor_name, coming_from,
 mobile, whom_to_meet, host_department_id, purpose, id_proof_type,
 id_proof_number, badge_no, created_by)
SELECT 'VIS-2526-00001', DATETIME('now', '-3 hours'), DATETIME('now', '-2 hours'),
       'Print Solutions Ltd', 'Arun Mehta', 'Pune', '9876500002',
       'Purchase Manager', d.id, 'Rate discussion', 'Aadhaar',
       'XXXX-XXXX-1234', 'B-201', u.id
FROM department d, app_user u
WHERE d.code='PLAN' AND u.username='admin';
