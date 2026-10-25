-- ============================================================
-- SEED: engineering (BOM template + 4 lines for A5 notebook)
-- ============================================================

INSERT OR IGNORE INTO bom_template
(bom_id, bom_group_id, product_category, product_group_name, size, pages,
 ruling_type, binding_type, docstatus)
VALUES ('BOM-TPL-NB-A5-192-SL-SPIRAL','A5-192-SL-SPIRAL','Notebook','A5 Spiral',
        'A5',192,'Single Line','Spiral',1);

-- Line 1: inner paper
INSERT OR IGNORE INTO bom_template_line
(bom_template_id, line_no, line_type, spec_material_group, spec_physical_form,
 spec_width_cm, spec_length_cm, spec_gsm, spec_paper_type, spec_signature,
 material_id, uom_id, base_qty_per_1000, wastage_pct, loss_pct,
 effective_qty_per_1000, process_stage)
SELECT bt.id, 1, 'raw_material', 'paper_inner', 'sheet', 70, 100, 80, 'maplitho',
       'paper_inner|sheet|70|100|80|maplitho',
       m.id, 1, 479.00, 5.0, 2.0, 513.00, 'Printing'
FROM bom_template bt, material m
WHERE bt.bom_id='BOM-TPL-NB-A5-192-SL-SPIRAL' AND m.code='PAP-080-70-100';

-- Line 2: cover paper
INSERT OR IGNORE INTO bom_template_line
(bom_template_id, line_no, line_type, spec_material_group, spec_physical_form,
 spec_width_cm, spec_length_cm, spec_gsm, spec_paper_type, spec_signature,
 material_id, uom_id, base_qty_per_1000, wastage_pct, loss_pct,
 effective_qty_per_1000, process_stage)
SELECT bt.id, 2, 'raw_material', 'paper_cover', 'sheet', 70, 100, 250, 'art_card',
       'paper_cover|sheet|70|100|250|art_card',
       m.id, 1, 12.00, 4.0, 1.0, 12.60, 'Cover Printing'
FROM bom_template bt, material m
WHERE bt.bom_id='BOM-TPL-NB-A5-192-SL-SPIRAL' AND m.code='PAP-250-70-100';

-- Line 3: carton
INSERT OR IGNORE INTO bom_template_line
(bom_template_id, line_no, line_type, spec_material_group, spec_physical_form,
 spec_width_cm, spec_length_cm, spec_height_cm, spec_ply, spec_signature,
 material_id, uom_id, base_qty_per_1000, wastage_pct, loss_pct,
 effective_qty_per_1000, process_stage)
SELECT bt.id, 3, 'consumable', 'carton', 'carton', 42, 34, 21.5, 3,
       'carton|carton|42|34|21.5|3',
       m.id, 2, 50.00, 1.0, 0.5, 50.75, 'Packing'
FROM bom_template bt, material m
WHERE bt.bom_id='BOM-TPL-NB-A5-192-SL-SPIRAL' AND m.code='CTN-42-34-21.5-3P';

-- Line 4: black ink
INSERT OR IGNORE INTO bom_template_line
(bom_template_id, line_no, line_type, spec_material_group, spec_physical_form,
 spec_ink_color, spec_ink_type, spec_signature,
 material_id, uom_id, base_qty_per_1000, wastage_pct, loss_pct,
 effective_qty_per_1000, process_stage)
SELECT bt.id, 4, 'consumable', 'ink', 'liquid', 'black', 'offset',
       'ink|liquid|black|offset',
       m.id, 5, 0.80, 5.0, 2.0, 0.86, 'Printing'
FROM bom_template bt, material m
WHERE bt.bom_id='BOM-TPL-NB-A5-192-SL-SPIRAL' AND m.code='INK-BLACK-OFFSET';
