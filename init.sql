-- Initialize messaging service database
-- This file is executed automatically when the PostgreSQL container starts

-- Ensure the database exists (it should already be created by the environment variables)
-- If not exists, it will be created by the POSTGRES_DB environment variable

-- Create any additional configurations if needed
-- The tables will be created by the Flask application using SQLAlchemy

-- Log that initialization is complete
SELECT 'Database initialization complete' as status;