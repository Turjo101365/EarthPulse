-- =============================================================================
-- EarthPulse 3D: NASA Multi-Sensor Geospatial Database Initialization
-- Includes pgvector extension for RAG embeddings & spatial indexing
-- =============================================================================

-- Enable pgvector extension for high-performance similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Active Satellite Fire Hotspots Table
CREATE TABLE IF NOT EXISTS hotspots (
    id VARCHAR(128) PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    brightness DOUBLE PRECISION,
    frp DOUBLE PRECISION DEFAULT 0.0,
    confidence DOUBLE PRECISION DEFAULT 80.0,
    acq_date VARCHAR(32),
    acq_time VARCHAR(32),
    satellite VARCHAR(64),
    instrument VARCHAR(64),
    daynight VARCHAR(16),
    risk_level VARCHAR(32),
    h3_index VARCHAR(64),
    raw_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Spatial and Telemetry Indexes for fast bounding box filtering
CREATE INDEX IF NOT EXISTS idx_hotspots_coords ON hotspots (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_hotspots_frp ON hotspots (frp);
CREATE INDEX IF NOT EXISTS idx_hotspots_satellite ON hotspots (satellite);
CREATE INDEX IF NOT EXISTS idx_hotspots_h3 ON hotspots (h3_index);

-- 2. RAG Knowledge Base & Embeddings (Vector Database)
CREATE TABLE IF NOT EXISTS rag_embeddings (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(64),
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. PulseAI Copilot & Incident Logs
CREATE TABLE IF NOT EXISTS chat_audit_logs (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64),
    user_query TEXT NOT NULL,
    copilot_response TEXT NOT NULL,
    model VARCHAR(64),
    latency_ms DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial test verification row
INSERT INTO hotspots (id, latitude, longitude, brightness, frp, confidence, acq_date, acq_time, satellite, instrument, daynight, risk_level, h3_index)
VALUES ('NASA_TEST_001', 23.8103, 90.4125, 335.5, 45.2, 92.0, '2026-10-07', '12:00', 'NOAA-20', 'VIIRS', 'D', 'HIGH', '8828308281fffff')
ON CONFLICT (id) DO NOTHING;
