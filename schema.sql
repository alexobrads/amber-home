-- Amber-Home Database Schema for PostgreSQL
-- Updated for Amber Electric API v2.0.12 with enhanced fields

CREATE TABLE IF NOT EXISTS sites (
    id VARCHAR PRIMARY KEY,
    nmi VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    nem_time TIMESTAMP WITH TIME ZONE NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    channel_type VARCHAR NOT NULL,
    per_kwh DECIMAL(10,5) NOT NULL,
    spot_per_kwh DECIMAL(10,5) NOT NULL,
    renewables DECIMAL(5,2),
    spike_status VARCHAR,
    descriptor VARCHAR,
    estimate BOOLEAN DEFAULT FALSE,
    var_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, nem_time, channel_type)
);

CREATE TABLE IF NOT EXISTS usage_data (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR NOT NULL,
    nem_time TIMESTAMP WITH TIME ZONE NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    channel_id VARCHAR,
    channel_type VARCHAR NOT NULL,
    kwh DECIMAL(10,5) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    quality VARCHAR,
    descriptor VARCHAR,
    var_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, nem_time, channel_id)
);

CREATE TABLE IF NOT EXISTS tariff_information (
    id SERIAL PRIMARY KEY,
    usage_id INTEGER,
    price_id INTEGER,
    period VARCHAR,
    season VARCHAR,
    block INTEGER,
    demand_window BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE price_data ADD CONSTRAINT fk_price_site 
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;

ALTER TABLE usage_data ADD CONSTRAINT fk_usage_site 
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE;