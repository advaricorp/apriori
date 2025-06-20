-- Inicialización de base de datos PostgreSQL para Apriori
-- Este script se ejecuta automáticamente cuando se crea el contenedor

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Crear usuario de aplicación si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'apriori_user') THEN
        CREATE ROLE apriori_user WITH LOGIN PASSWORD 'apriori_secure_password_2024';
    END IF;
END
$$;

-- Asegurar permisos en la base de datos
GRANT ALL PRIVILEGES ON DATABASE apriori_db TO apriori_user;
GRANT ALL ON SCHEMA public TO apriori_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO apriori_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO apriori_user;

-- Configuraciones de performance
ALTER DATABASE apriori_db SET default_text_search_config = 'spanish';

-- Datos de inicialización para desarrollo
INSERT INTO organizations (name, slug, domain, is_active, settings, created_at, updated_at) 
VALUES 
    ('IPS Seguridad', 'ips-seguridad', 'ips.apriori.enkisys.com', true, '{}', NOW(), NOW()),
    ('Demo Organization', 'demo', 'demo.apriori.enkisys.com', true, '{}', NOW(), NOW())
ON CONFLICT (slug) DO NOTHING;

-- Crear usuario administrador por defecto (password: admin123)
-- Hash bcrypt para 'admin123': $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBdXzogKLzOKte
INSERT INTO users (email, username, hashed_password, full_name, is_active, is_superuser, organization_id, role, created_at, updated_at)
VALUES 
    ('admin@ips.com', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBdXzogKLzOKte', 'Administrador IPS', true, true, 1, 'admin', NOW(), NOW()),
    ('demo@demo.com', 'demo', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewdBdXzogKLzOKte', 'Usuario Demo', true, false, 2, 'admin', NOW(), NOW())
ON CONFLICT (email) DO NOTHING;

-- Configurar timezone por defecto
SET timezone = 'America/Mexico_City';

-- Función para actualizar timestamps automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Comentarios sobre la estructura
COMMENT ON DATABASE apriori_db IS 'Base de datos para sistema Apriori - Análisis de entrevistas de salida con IA';
COMMENT ON SCHEMA public IS 'Schema principal con todas las tablas de la aplicación'; 