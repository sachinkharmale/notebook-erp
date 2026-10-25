-- ============================================================
-- VIEWS for production reporting
-- ============================================================

CREATE VIEW IF NOT EXISTS v_wos_rollup AS
SELECT
    w.id                                                        AS wos_id,
    w.wos_no,
    w.order_qty,
    w.wos_status,
    COALESCE((SELECT SUM(qty_produced) FROM production_entry
              WHERE wos_id = w.id AND docstatus = 1), 0)        AS qty_produced,
    COALESCE((SELECT SUM(qty_packed) FROM packing_entry
              WHERE wos_id = w.id AND docstatus = 1), 0)        AS qty_packed,
    COALESCE((SELECT SUM(qty_dispatched) FROM dispatch_entry
              WHERE wos_id = w.id AND docstatus = 1), 0)        AS qty_dispatched,
    w.order_qty - COALESCE((SELECT SUM(qty_dispatched) FROM dispatch_entry
              WHERE wos_id = w.id AND docstatus = 1), 0)        AS qty_balance
FROM wos w;

CREATE VIEW IF NOT EXISTS v_indent_rollup AS
SELECT
    il.id                                                       AS indent_line_id,
    il.indent_id,
    il.material_id,
    il.qty_approved,
    COALESCE(SUM(mil.qty_issued), 0)                            AS qty_issued,
    il.qty_approved - COALESCE(SUM(mil.qty_issued), 0)          AS qty_pending,
    CASE
        WHEN COALESCE(SUM(mil.qty_issued), 0) = 0
            THEN 'pending'
        WHEN COALESCE(SUM(mil.qty_issued), 0) < il.qty_approved
            THEN 'partial'
        ELSE 'full'
    END                                                         AS issue_status
FROM indent_line il
LEFT JOIN material_issue_line mil ON mil.indent_line_id = il.id
LEFT JOIN material_issue mi ON mi.id = mil.material_issue_id AND mi.docstatus = 1
GROUP BY il.id, il.indent_id, il.material_id, il.qty_approved;

CREATE VIEW IF NOT EXISTS v_supplier_po_rollup AS
SELECT
    spl.id                                                      AS po_line_id,
    spl.supplier_po_id,
    spl.material_id,
    spl.order_qty,
    COALESCE(SUM(gl.qty_received), 0)                           AS qty_received,
    spl.order_qty - COALESCE(SUM(gl.qty_received), 0)           AS qty_balance
FROM supplier_po_line spl
LEFT JOIN grn_line gl ON gl.supplier_po_line_id = spl.id
LEFT JOIN grn g ON g.id = gl.grn_id AND g.docstatus = 1
GROUP BY spl.id, spl.supplier_po_id, spl.material_id, spl.order_qty;
