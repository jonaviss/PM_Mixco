-- ===============================================================
-- Índices de performance para ERP Visoni
-- Ejecutar en el editor SQL de Supabase (una sola vez)
-- ===============================================================

-- 1. Búsquedas por comprador (cancelar venta, cliente compras, reportes)
CREATE INDEX IF NOT EXISTS idx_ventas_comprador ON libreria_ventas (comprador_cui);

-- 2. Ordenamiento por fecha (dashboard, reportes, paginación)
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON libreria_ventas (created_at DESC);

-- 3. Filtro por estado de pago (créditos pendientes)
CREATE INDEX IF NOT EXISTS idx_ventas_estado_pago ON libreria_ventas (estado_pago);

-- 4. Filtro por digitador (rol cajero/encargado)
CREATE INDEX IF NOT EXISTS idx_ventas_digitado_por ON libreria_ventas (digitado_por);

-- 5. Detalle de venta por venta_id (unión con ventas)
CREATE INDEX IF NOT EXISTS idx_detalle_venta ON libreria_ventas_detalle (venta_id);

-- 6. Lotes por producto (FIFO)
CREATE INDEX IF NOT EXISTS idx_lotes_producto ON lotes (producto_id);

-- 7. Pagos por venta
CREATE INDEX IF NOT EXISTS idx_pagos_venta ON libreria_pagos (venta_id);

-- 8. Categoría de producto (filtro en inventario)
CREATE INDEX IF NOT EXISTS idx_inventario_tipo ON inventario_libreria (tipo_producto);

-- 9. Comprador + fecha compuesto (consultas más comunes)
CREATE INDEX IF NOT EXISTS idx_ventas_comprador_fecha ON libreria_ventas (comprador_cui, created_at DESC);
