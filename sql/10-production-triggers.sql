-- ============================================================
-- PRODUCTION TRIGGERS
-- R1: issue <= approved
-- R2: dispatch <= packed
-- R3: packed <= produced
-- R4: production requires material issued
-- R10: issue submit → stock ledger
-- ============================================================

-- R1: Block over-issue against an indent line
CREATE TRIGGER IF NOT EXISTS trg_r1_issue_qty
BEFORE INSERT ON material_issue_line
FOR EACH ROW
WHEN (SELECT COALESCE(SUM(qty_issued), 0) FROM material_issue_line
      WHERE indent_line_id = NEW.indent_line_id) + NEW.qty_issued
   > (SELECT COALESCE(qty_approved, 0) FROM indent_line WHERE id = NEW.indent_line_id)
BEGIN
    SELECT RAISE(ABORT, 'R1: Issue qty exceeds approved qty for indent line');
END;

-- R2: Block over-dispatch beyond packed qty
CREATE TRIGGER IF NOT EXISTS trg_r2_dispatch_qty
BEFORE INSERT ON dispatch_entry
FOR EACH ROW
WHEN NEW.docstatus = 1
     AND (SELECT COALESCE(SUM(qty_dispatched), 0) FROM dispatch_entry
          WHERE wos_id = NEW.wos_id AND docstatus = 1) + NEW.qty_dispatched
       > (SELECT COALESCE(SUM(qty_packed), 0) FROM packing_entry
          WHERE wos_id = NEW.wos_id AND docstatus = 1)
BEGIN
    SELECT RAISE(ABORT, 'R2: Dispatch qty exceeds packed qty for WOS');
END;

-- R3: Block over-packing beyond produced qty
CREATE TRIGGER IF NOT EXISTS trg_r3_pack_qty
BEFORE INSERT ON packing_entry
FOR EACH ROW
WHEN NEW.docstatus = 1
     AND (SELECT COALESCE(SUM(qty_packed), 0) FROM packing_entry
          WHERE wos_id = NEW.wos_id AND docstatus = 1) + NEW.qty_packed
       > (SELECT COALESCE(SUM(qty_produced), 0) FROM production_entry
          WHERE wos_id = NEW.wos_id AND docstatus = 1)
BEGIN
    SELECT RAISE(ABORT, 'R3: Packing qty exceeds produced qty for WOS');
END;

-- R4: Block production without material issued
CREATE TRIGGER IF NOT EXISTS trg_r4_production_issue
BEFORE INSERT ON production_entry
FOR EACH ROW
WHEN NEW.docstatus = 1
     AND NOT EXISTS (SELECT 1 FROM material_issue
                     WHERE wos_id = NEW.wos_id AND docstatus = 1)
BEGIN
    SELECT RAISE(ABORT, 'R4: Cannot produce without material issued for WOS');
END;

-- R10: Material Issue submit → post stock ledger (out)
CREATE TRIGGER IF NOT EXISTS trg_r10_issue_submit
AFTER UPDATE OF docstatus ON material_issue
FOR EACH ROW
WHEN NEW.docstatus = 1 AND OLD.docstatus = 0
BEGIN
    INSERT INTO stock_ledger (
        txn_date, material_id, warehouse_id,
        qty_in, qty_out, txn_type, ref_doctype, ref_id, created_by
    )
    SELECT
        NEW.issue_date,
        mil.material_id,
        NEW.warehouse_id,
        0,
        mil.qty_issued,
        'material_issue',
        'material_issue',
        NEW.id,
        NEW.created_by
    FROM material_issue_line mil
    WHERE mil.material_issue_id = NEW.id;
END;
