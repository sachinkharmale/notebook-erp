-- ============================================================
-- FINANCE VIEWS — invoice status + aging (2 views)
-- ============================================================

CREATE VIEW IF NOT EXISTS v_sales_invoice_status AS
SELECT
    si.*,
    COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
              WHERE invoice_type = 'sales_invoice' AND invoice_id = si.id), 0)
                                                                AS paid_amount,
    si.total_amount - COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
              WHERE invoice_type = 'sales_invoice' AND invoice_id = si.id), 0)
                                                                AS balance,
    CASE
        WHEN COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
                       WHERE invoice_type = 'sales_invoice' AND invoice_id = si.id), 0)
             >= si.total_amount THEN 'paid'
        WHEN COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
                       WHERE invoice_type = 'sales_invoice' AND invoice_id = si.id), 0)
             > 0 THEN 'partially_paid'
        WHEN si.due_date IS NOT NULL AND si.due_date < DATE('now')
             AND COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
                           WHERE invoice_type = 'sales_invoice' AND invoice_id = si.id), 0)
                 < si.total_amount THEN 'overdue'
        ELSE 'sent'
    END                                                         AS computed_status
FROM sales_invoice si;

CREATE VIEW IF NOT EXISTS v_purchase_invoice_status AS
SELECT
    pi.*,
    COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
              WHERE invoice_type = 'purchase_invoice' AND invoice_id = pi.id), 0)
                                                                AS paid_amount,
    pi.total_amount - COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
              WHERE invoice_type = 'purchase_invoice' AND invoice_id = pi.id), 0)
                                                                AS balance,
    CASE
        WHEN COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
                       WHERE invoice_type = 'purchase_invoice' AND invoice_id = pi.id), 0)
             >= pi.total_amount THEN 'paid'
        WHEN COALESCE((SELECT SUM(allocated_amount) FROM payment_allocation
                       WHERE invoice_type = 'purchase_invoice' AND invoice_id = pi.id), 0)
             > 0 THEN 'partially_paid'
        ELSE 'unpaid'
    END                                                         AS computed_status
FROM purchase_invoice pi;
