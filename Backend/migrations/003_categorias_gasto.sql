CREATE TABLE IF NOT EXISTS categorias_gasto (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO categorias_gasto (nombre) VALUES
    ('Papelería'),
    ('Limpieza'),
    ('Servicios'),
    ('Transporte'),
    ('Alimentación'),
    ('Mantenimiento'),
    ('Otro')
ON CONFLICT (nombre) DO NOTHING;
