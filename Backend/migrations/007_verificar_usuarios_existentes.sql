-- ============================================
-- MARCAR USUARIOS EXISTENTES COMO VERIFICADOS
-- Ejecutar DESPUÉS de 006_verificacion_correo.sql
-- ============================================

UPDATE usuarios SET verificado = true WHERE verificado IS NULL OR verificado = false;
