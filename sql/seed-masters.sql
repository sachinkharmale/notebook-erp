-- ============================================================
-- Seed data for masters (Phase 1)
-- ============================================================

-- UOM
INSERT OR IGNORE INTO uom (code, name) VALUES
('KG','Kilogram'),('PCS','Pieces'),('SHEET','Sheet'),
('REEL','Reel'),('LTR','Litre'),('ROLL','Roll');

-- Departments
INSERT OR IGNORE INTO department (code, name) VALUES
('SALES','Sales'),('PLAN','Planning'),('STORE','Store'),
('PROD','Production'),('QC','Quality Control'),('DISP','Dispatch'),
('GATE','Security'),('ADMIN','Administration');

-- Warehouses
INSERT OR IGNORE INTO warehouse (code, name, is_consumable_store) VALUES
('WH-RM-01','Raw Material Store',0),
('WH-CON-01','Consumables Store',1),
('WH-FG-01','Finished Goods Store',0);

-- Admin user (password will be set by init script)
INSERT OR IGNORE INTO app_user (username, password_hash, full_name, role) VALUES
('admin','CHANGE_ME_ON_FIRST_RUN','Administrator','admin');

-- Cost Centers
INSERT OR IGNORE INTO cost_center (code, name, category) VALUES
('CC-ADMIN','Administration','admin'),
('CC-SALES','Sales & Marketing','sales'),
('CC-STORE','Stores & Warehouse','service'),
('CC-PRINT','Printing','production'),
('CC-CUT','Cutting & Trimming','production'),
('CC-BIND','Binding','production'),
('CC-PACK','Packing','production'),
('CC-QC','Quality Control','service'),
('CC-DISP','Dispatch','service');

-- Sample materials (paper, cartons, ink, plates, wire)
INSERT OR IGNORE INTO material
(code, name, spec_signature, category, material_group, uom_id,
 physical_form, width_cm, length_cm, gsm, paper_type, is_inner_page) VALUES
('PAP-070-70-100','Paper 70 GSM Maplitho 70x100','paper_inner|sheet|70|100|70|maplitho',
 'raw_material','paper_inner',1,'sheet',70,100,70,'maplitho',1),
('PAP-080-70-100','Paper 80 GSM Maplitho 70x100','paper_inner|sheet|70|100|80|maplitho',
 'raw_material','paper_inner',1,'sheet',70,100,80,'maplitho',1),
('PAP-250-70-100','Art Card 250 GSM 70x100','paper_cover|sheet|70|100|250|art_card',
 'raw_material','paper_cover',1,'sheet',70,100,250,'art_card',0);

INSERT OR IGNORE INTO material
(code, name, spec_signature, category, material_group, uom_id,
 physical_form, width_cm, length_cm, height_cm, ply) VALUES
('CTN-42-34-21.5-3P','Carton 42x34x21.5 cm 3-ply','carton|carton|42|34|21.5|3',
 'consumable','carton',2,'carton',42,34,21.5,3),
('CTN-47-32.5-18-3P','Carton 47x32.5x18 cm 3-ply','carton|carton|47|32.5|18|3',
 'consumable','carton',2,'carton',47,32.5,18,3);

INSERT OR IGNORE INTO material
(code, name, spec_signature, category, material_group, uom_id,
 physical_form, ink_color, ink_type) VALUES
('INK-CYAN-OFFSET','Offset Ink Cyan','ink|liquid|cyan|offset',
 'consumable','ink',5,'liquid','cyan','offset'),
('INK-BLACK-OFFSET','Offset Ink Black','ink|liquid|black|offset',
 'consumable','ink',5,'liquid','black','offset');

INSERT OR IGNORE INTO material
(code, name, spec_signature, category, material_group, uom_id,
 physical_form, plate_size) VALUES
('PLT-GTO52-CTP','CTP Plate GTO-52','plate|plate|GTO-52',
 'consumable','plate',2,'plate','GTO-52');
