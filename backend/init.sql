-- I.A Priori Database Initialization Script
-- This script sets up the initial database structure and default data

-- Set locale and encoding
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable Spanish language support (PostgreSQL 15 compatible)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'spanish_config') THEN
        CREATE TEXT SEARCH CONFIGURATION spanish_config (COPY = spanish);
    END IF;
END $$;

-- Performance optimizations
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Create default organization (IPS)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
        -- Tables will be created by Alembic migrations
        RAISE NOTICE 'Tables will be created by Alembic migrations';
    END IF;
END $$;

-- Insert default data after tables are created
-- This will be executed after Alembic migrations
CREATE OR REPLACE FUNCTION insert_default_data()
RETURNS void AS $$
DECLARE
    org_id UUID;
    admin_id UUID;
BEGIN
    -- Check if organizations table exists and insert default org
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
        -- Insert default organization if not exists
        INSERT INTO organizations (id, name, domain, settings, created_at, updated_at)
        VALUES (
            uuid_generate_v4(),
            'IPS - Integrated Professional Services',
            'ips.com',
            '{"theme": "matrix", "language": "es", "timezone": "America/Mexico_City"}',
            NOW(),
            NOW()
        ) ON CONFLICT (domain) DO NOTHING
        RETURNING id INTO org_id;
        
        -- Get org_id if already exists
        IF org_id IS NULL THEN
            SELECT id INTO org_id FROM organizations WHERE domain = 'ips.com';
        END IF;
        
        -- Insert default admin user if not exists
        INSERT INTO users (id, email, hashed_password, full_name, role, organization_id, is_active, created_at, updated_at)
        VALUES (
            uuid_generate_v4(),
            'admin@ips.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvyBdm9SyXkEGYa', -- password: admin123
            'Administrador del Sistema',
            'admin',
            org_id,
            true,
            NOW(),
            NOW()
        ) ON CONFLICT (email) DO NOTHING;
        
        -- Insert demo manager user
        INSERT INTO users (id, email, hashed_password, full_name, role, organization_id, is_active, created_at, updated_at)
        VALUES (
            uuid_generate_v4(),
            'manager@ips.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewvyBdm9SyXkEGYa', -- password: admin123
            'Gerente de Recursos Humanos',
            'manager',
            org_id,
            true,
            NOW(),
            NOW()
        ) ON CONFLICT (email) DO NOTHING;
        
        -- Insert demo employees
        INSERT INTO employees (id, email, full_name, department, position, hire_date, phone, organization_id, is_active, created_at, updated_at)
        VALUES 
        (
            uuid_generate_v4(),
            'juan.perez@ips.com',
            'Juan Pérez García',
            'Desarrollo',
            'Desarrollador Senior',
            '2022-01-15',
            '+52 55 1234 5678',
            org_id,
            true,
            NOW(),
            NOW()
        ),
        (
            uuid_generate_v4(),
            'maria.rodriguez@ips.com',
            'María Rodríguez López',
            'Marketing',
            'Especialista en Marketing Digital',
            '2021-06-10',
            '+52 55 2345 6789',
            org_id,
            true,
            NOW(),
            NOW()
        ),
        (
            uuid_generate_v4(),
            'carlos.martinez@ips.com',
            'Carlos Martínez Hernández',
            'Ventas',
            'Ejecutivo de Ventas',
            '2023-03-20',
            '+52 55 3456 7890',
            org_id,
            true,
            NOW(),
            NOW()
        ) ON CONFLICT (email) DO NOTHING;
        
        RAISE NOTICE 'Default data inserted successfully';
    ELSE
        RAISE NOTICE 'Organizations table does not exist yet. Default data will be inserted after migrations.';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance (will be created after tables exist)
CREATE OR REPLACE FUNCTION create_performance_indexes()
RETURNS void AS $$
BEGIN
    -- Check if tables exist before creating indexes
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'interviews') THEN
        CREATE INDEX IF NOT EXISTS idx_interviews_organization_id ON interviews(organization_id);
        CREATE INDEX IF NOT EXISTS idx_interviews_created_at ON interviews(created_at);
        CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
        CREATE INDEX IF NOT EXISTS idx_interviews_sentiment ON interviews(sentiment);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'employees') THEN
        CREATE INDEX IF NOT EXISTS idx_employees_organization_id ON employees(organization_id);
        CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
        CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active);
        CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX IF NOT EXISTS idx_users_organization_id ON users(organization_id);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'analyses') THEN
        CREATE INDEX IF NOT EXISTS idx_analyses_interview_id ON analyses(interview_id);
        CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);
    END IF;
    
    RAISE NOTICE 'Performance indexes created successfully';
END;
$$ LANGUAGE plpgsql;

-- Create a function to be called after migrations
CREATE OR REPLACE FUNCTION setup_apriori_database()
RETURNS void AS $$
BEGIN
    PERFORM insert_default_data();
    PERFORM create_performance_indexes();
    RAISE NOTICE 'I.A Priori database setup completed successfully';
END;
$$ LANGUAGE plpgsql;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'I.A Priori database initialization script completed';
    RAISE NOTICE 'Run SELECT setup_apriori_database(); after Alembic migrations to insert default data';
END $$; 