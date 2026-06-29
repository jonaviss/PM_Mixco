-- ============================================
-- LIMPIAR DATOS TRANSACCIONALES
-- Conserva catálogos, usuarios y accesos.
-- Deja usuario 2263336201105 como super_admin.
-- ============================================

-- 1. LIMPIAR DATOS TRANSACCIONALES
DELETE FROM libreria_ventas_detalle;
DELETE FROM libreria_pagos;
DELETE FROM libreria_ventas;
DELETE FROM lotes;
DELETE FROM compras_detalle;
DELETE FROM compras;
DELETE FROM pagos_proveedores;
DELETE FROM gastos;

-- 2. REINICIAR SEQUENCES (ajustar según los IDs actuales de tus catálogos)
ALTER SEQUENCE IF EXISTS categorias_gasto_id_seq RESTART WITH 8;
ALTER SEQUENCE IF EXISTS tipos_producto_id_seq RESTART WITH 6;
ALTER SEQUENCE IF EXISTS cat_metodos_pago_id_seq RESTART WITH 4;

-- 3. VERIFICACIÓN
-- SELECT * FROM usuarios WHERE cui = '2263336201105';
-- SELECT COUNT(*) as transacciones FROM libreria_ventas;
