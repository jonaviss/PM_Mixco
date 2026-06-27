-- ============================================
-- RESET DE BASE DE DATOS PARA ENTREGA
-- Limpia datos transaccionales, conserva
-- catálogos y usuario admin, e inserta
-- datos de muestra para exploración.
-- ============================================

-- 1. LIMPIAR DATOS TRANSACCIONALES
DELETE FROM libreria_ventas_detalle;
DELETE FROM libreria_pagos;
DELETE FROM libreria_ventas;
DELETE FROM lotes;
DELETE FROM compras_detalle;
DELETE FROM compras;
DELETE FROM pagos_proveedores;
DELETE FROM proveedores;
DELETE FROM gastos;
DELETE FROM inventario_libreria;
DELETE FROM reset_tokens;

-- 2. CONSERVAR SOLO USUARIO ADMIN (2263336201105)
DELETE FROM accesos_usuarios WHERE usuario_cui != '2263336201105';
DELETE FROM usuarios WHERE cui != '2263336201105';

-- 3. REINICIAR SEQUENCES
ALTER SEQUENCE IF EXISTS categorias_gasto_id_seq RESTART WITH 8;
ALTER SEQUENCE IF EXISTS tipos_producto_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS cat_metodos_pago_id_seq RESTART WITH 1;

-- 4. DATOS DE MUESTRA: TIPOS DE PRODUCTO (si está vacío)
INSERT INTO tipos_producto (nombre) VALUES
    ('Biblia'), ('Himno'), ('Libro'), ('Material'), ('Accesorio')
ON CONFLICT (nombre) DO NOTHING;

-- 5. DATOS DE MUESTRA: MÉTODOS DE PAGO (si está vacío)
INSERT INTO cat_metodos_pago (nombre) VALUES
    ('Efectivo'), ('Tarjeta Débito/Crédito'), ('Transferencia')
ON CONFLICT (nombre) DO NOTHING;

-- 6. DATOS DE MUESTRA: CATEGORÍAS DE GASTO (si está vacío)
INSERT INTO categorias_gasto (nombre) VALUES
    ('Papelería'), ('Limpieza'), ('Servicios'),
    ('Transporte'), ('Alimentación'), ('Mantenimiento'), ('Otro')
ON CONFLICT (nombre) DO NOTHING;

-- 7. DATOS DE MUESTRA: PROVEEDORES
INSERT INTO proveedores (nombre, contacto, telefono, activo) VALUES
    ('Distribuidora Cristiana GT', 'Carlos López', '5555-0101', true),
    ('Librería Bet-El Mayorista', 'María García', '5555-0102', true);

-- 8. DATOS DE MUESTRA: PRODUCTOS
INSERT INTO inventario_libreria (tipo_producto, nombre, descripcion, precio, stock, estado) VALUES
    ('Biblia', 'Biblia Reina Valera 1960 - Piel', 'Biblia en cuero, letra grande', 85.00, 10, true),
    ('Biblia', 'Biblia Reina Valera 1995 - Tapa Dura', 'Biblia de estudio', 95.00, 8, true),
    ('Himno', 'Himnario Bautista Clásico', 'Himnario tradicional', 45.00, 15, true),
    ('Libro', 'El Progreso del Peregrino', 'Libro clásico cristiano', 35.00, 20, true),
    ('Libro', 'Mero Cristianismo - C.S. Lewis', 'Apologética cristiana', 40.00, 12, true),
    ('Material', 'Juego de Marcadores Bíblicos', 'Set de 6 marcadores', 15.00, 30, true),
    ('Accesorio', 'Funda para Biblia', 'Funda de cuero', 25.00, 18, true);

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- SELECT COUNT(*) as usuarios FROM usuarios;
-- SELECT COUNT(*) as productos FROM inventario_libreria;
-- SELECT COUNT(*) as proveedores FROM proveedores;
