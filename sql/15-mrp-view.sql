-- ============================================================
-- MRP VIEW — aggregated material demand across all open WOS
-- ============================================================

CREATE VIEW IF NOT EXISTS v_material_requirement AS
SELECT
    wbl.material_id,
    m.code AS material_code,
    m.name AS material_name,
    m.uom_id,
    m.category AS material_category,
    m.material_group,
    SUM(wbl.required_qty) AS total_required_qty,
    COALESCE(MAX(issued.total_issued), 0) AS qty_already_issued,
    SUM(wbl.required_qty) - COALESCE(MAX(issued.total_issued), 0) AS qty_still_needed,
    COALESCE(MAX(stock.available_qty), 0) AS stock_on_hand,
    CASE
        WHEN SUM(wbl.required_qty) - COALESCE(MAX(issued.total_issued), 0)
             - COALESCE(MAX(stock.available_qty), 0) > 0
        THEN SUM(wbl.required_qty) - COALESCE(MAX(issued.total_issued), 0)
             - COALESCE(MAX(stock.available_qty), 0)
        ELSE 0
    END AS qty_to_procure,
    MIN(w.ship_date) AS earliest_need_by,
    COUNT(DISTINCT w.id) AS wos_count,
    GROUP_CONCAT(DISTINCT w.wos_no) AS wos_list
FROM wos_bom_line wbl
JOIN wos_bom wb ON wb.id = wbl.wos_bom_id
JOIN wos w ON w.id = wb.wos_id
JOIN material m ON m.id = wbl.material_id
LEFT JOIN (
    SELECT mil.material_id, SUM(mil.qty_issued) AS total_issued
    FROM material_issue_line mil
    JOIN material_issue mi ON mi.id = mil.material_issue_id AND mi.docstatus = 1
    GROUP BY mil.material_id
) issued ON issued.material_id = wbl.material_id
LEFT JOIN (
    SELECT material_id, SUM(qty_in - qty_out) AS available_qty
    FROM stock_ledger
    GROUP BY material_id
) stock ON stock.material_id = wbl.material_id
WHERE w.docstatus = 1
  AND w.wos_status NOT IN ('dispatched','closed','cancelled')
GROUP BY wbl.material_id, m.code, m.name, m.uom_id, m.category, m.material_group;
