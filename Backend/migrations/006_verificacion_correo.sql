-- ============================================
-- VERIFICACIÓN DE CORREO ELECTRÓNICO
-- Agrega columna verificado a usuarios + tabla
-- para tokens de verificación.
-- ============================================

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS verificado BOOLEAN DEFAULT false;

CREATE TABLE IF NOT EXISTS verificacion_tokens (
    id BIGSERIAL PRIMARY KEY,
    cui TEXT NOT NULL REFERENCES usuarios(cui) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_verificacion_tokens_hash ON verificacion_tokens(token_hash);
