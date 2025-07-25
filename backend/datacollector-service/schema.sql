-- Amber-Home Database Schema for PostgreSQL
-- Updated for Amber Electric API v2.0.12 with enhanced fields

CREATE TABLE IF NOT EXISTS sites (
    id VARCHAR PRIMARY KEY,
    nmi VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price data table matching Amber Electric API schema exactly
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

-- Price forecast data table for storing ForecastInterval and CurrentInterval data
CREATE TABLE IF NOT EXISTS price_forecasts (
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
    -- Forecast-specific fields
    forecast_type VARCHAR NOT NULL, -- 'ForecastInterval' or 'CurrentInterval'
    range_low DECIMAL(10,5),
    range_high DECIMAL(10,5),
    advanced_price_low DECIMAL(10,5),
    advanced_price_predicted DECIMAL(10,5),
    advanced_price_high DECIMAL(10,5),
    forecast_generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    var_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(site_id, nem_time, channel_type, forecast_generated_at)
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_price_data_nem_time ON price_data(nem_time);
CREATE INDEX IF NOT EXISTS idx_price_data_site_channel ON price_data(site_id, channel_type);
CREATE INDEX IF NOT EXISTS idx_usage_data_nem_time ON usage_data(nem_time);
CREATE INDEX IF NOT EXISTS idx_usage_data_site_channel ON usage_data(site_id, channel_type);

-- Indexes for forecast data
CREATE INDEX IF NOT EXISTS idx_price_forecasts_nem_time ON price_forecasts(nem_time);
CREATE INDEX IF NOT EXISTS idx_price_forecasts_site_channel ON price_forecasts(site_id, channel_type);
CREATE INDEX IF NOT EXISTS idx_price_forecasts_generated_at ON price_forecasts(forecast_generated_at);
CREATE INDEX IF NOT EXISTS idx_price_forecasts_type ON price_forecasts(forecast_type);