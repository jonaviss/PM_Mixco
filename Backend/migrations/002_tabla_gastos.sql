-- Tabla de gastos de la librería
CREATE TABLE IF NOT EXISTS gastos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    descripcion TEXT NOT NULL,
    monto DECIMAL(12,2) NOT NULL CHECK (monto > 0),
    categoria TEXT NOT NULL DEFAULT 'Otro',
    fecha_gasto DATE NOT NULL DEFAULT CURRENT_DATE,
    registrado_por TEXT NOT NULL REFERENCES usuarios(cui),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos (fecha_gasto DESC);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria ON gastos (categoria);
