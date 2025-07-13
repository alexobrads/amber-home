-- Amber-Home Database Schema for PostgreSQL
-- Simple tables for home energy data collection

CREATE TABLE IF NOT EXISTS sites (
    id VARCHAR PRIMARY KEY,
    nmi VARCHAR,
    network VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    nem_time TIMESTAMP WITH TIME ZONE NOT NULL,
    channel_type VARCHAR NOT NULL,
    per_kwh DECIMAL(10,5) NOT NULL,
    spot_per_kwh DECIMAL(10,5) NOT NULL,
    renewables DECIMAL(5,2),
    spike_status VARCHAR,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, nem_time, channel_type)
);

CREATE TABLE IF NOT EXISTS usage_data (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    nem_time TIMESTAMP WITH TIME ZONE NOT NULL,
    channel_id VARCHAR NOT NULL,
    channel_type VARCHAR NOT NULL,
    kwh DECIMAL(10,5) NOT NULL,
    cost_dollars DECIMAL(10,2) NOT NULL,
    quality VARCHAR,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, nem_time, channel_id)
);

-- Foreign key constraints
ALTER TABLE price_data ADD CONSTRAINT fk_price_site 
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;

ALTER TABLE usage_data ADD CONSTRAINT fk_usage_site 
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;