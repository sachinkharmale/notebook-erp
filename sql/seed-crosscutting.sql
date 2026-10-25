-- ============================================================
-- SEED: naming series + role permissions
-- ============================================================

INSERT OR IGNORE INTO naming_series (entity, prefix, reset_period) VALUES
('customer_po',      'CPO', 'yearly'),
('wos',              'WOS', 'yearly'),
('bom_template',     'BOM', 'yearly'),
('supplier_po',      'SPO', 'yearly'),
('grn',              'GRN', 'yearly'),
('indent',           'IND', 'yearly'),
('material_issue',   'ISS', 'yearly'),
('production_entry', 'PRD', 'yearly'),
('packing_entry',    'PCK', 'yearly'),
('dispatch_entry',   'DSP', 'yearly'),
('qc_record',        'QC',  'yearly'),
('vehicle_visit',    'VEH', 'yearly'),
('visitor_visit',    'VIS', 'yearly'),
('sales_invoice',    'SI',  'yearly'),
('purchase_invoice', 'PI',  'yearly'),
('payment_entry',    'PAY', 'yearly');

INSERT OR IGNORE INTO role_permission
(role, doctype, can_read, can_create, can_edit, can_submit, can_cancel) VALUES
('admin',      '*',                 1, 1, 1, 1, 1),
('sales',      'customer_po',       1, 1, 1, 1, 0),
('sales',      'wos',               1, 1, 1, 0, 0),
('sales',      'sales_invoice',     1, 1, 1, 1, 0),
('planner',    'bom_template',      1, 1, 1, 1, 0),
('planner',    'supplier_po',       1, 1, 1, 1, 1),
('store',      'grn',               1, 1, 1, 1, 1),
('store',      'indent',            1, 1, 0, 0, 0),
('store',      'material_issue',    1, 1, 1, 1, 1),
('store',      'purchase_invoice',  1, 1, 1, 1, 0),
('production', 'production_entry',  1, 1, 1, 1, 0),
('production', 'packing_entry',     1, 1, 1, 1, 0),
('dispatch',   'dispatch_entry',    1, 1, 1, 1, 1),
('qc',         'qc_record',         1, 1, 1, 1, 0),
('gate',       'vehicle_visit',     1, 1, 1, 1, 0),
('gate',       'visitor_visit',     1, 1, 1, 1, 0),
('finance',    'sales_invoice',     1, 1, 1, 1, 1),
('finance',    'purchase_invoice',  1, 1, 1, 1, 1),
('finance',    'payment_entry',     1, 1, 1, 1, 1);
