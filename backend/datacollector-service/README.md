# Amber-Home Data Collector Service

A containerized backend service that automatically collects and stores energy data from the Amber Electric API.

## Overview

This service handles:
- Historical data initialization from a configurable start date
- Continuous data collection every 5 minutes (configurable)
- Separate tracking for price and usage data to handle data misalignment
- Raw API data storage without filtering or modifications
- Robust error handling and rate limiting

## Architecture

### Service Structure
```
services/datacollector-service/
├── app/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── database.py       # Database service layer
│   ├── main.py          # Application entry point
│   └── services.py      # Business logic services
├── amber_client.py      # Amber API client wrapper
├── schema.sql          # Database schema
├── main.py            # Container entry point
├── Dockerfile         # Container definition
├── docker-compose.yml # Service orchestration
└── pyproject.toml     # Dependencies
```

### Key Components

- **Config**: Centralized configuration with environment variable validation
- **DatabaseService**: Handles all database operations and connections
- **AmberService**: Manages Amber Electric API interactions
- **CollectionService**: Orchestrates data collection workflows

## Features

### Data Collection Strategy
- **Historical Initialization**: Collects all data from `HISTORICAL_START_DATE` on first run
- **Incremental Updates**: Collects new data since last successful collection
- **Separate Tracking**: Price and usage data tracked independently (usage typically 1 day behind)
- **Rate Limiting**: Respects Amber API limits (50 calls per 5 minutes, 7-day max ranges)

### Error Handling
- Graceful shutdown on SIGINT/SIGTERM
- Automatic retry on temporary failures
- Continues collection even if individual sites fail
- Comprehensive logging with configurable levels

### Data Storage
- Raw API data preservation (no filtering or derived fields)
- Duplicate handling with ON CONFLICT updates
- Foreign key constraints and data integrity
- Timezone-aware timestamps (NEM time + UTC)

## Configuration

### Required Environment Variables
```bash
AMBER_API_KEY=your_amber_api_key_here
DATABASE_URL=postgresql://user:pass@host:port/dbname
HISTORICAL_START_DATE=2024-01-01
```

### Optional Environment Variables
```bash
COLLECTION_INTERVAL_MINUTES=5    # Collection frequency
LOG_LEVEL=INFO                   # Logging level
FORCE_REINIT=false              # Force full data re-collection
```

## Deployment

### Local Development
```bash
# Copy environment template
cp .env.example .env.local

# Edit configuration
# Set AMBER_API_KEY, DATABASE_URL, HISTORICAL_START_DATE

# Run with uv
uv sync
uv run python main.py
```

### Docker Deployment
```bash
# Build and run
docker-compose up -d

# Monitor logs
docker-compose logs -f datacollector

# Stop service
docker-compose down
```

### Railway Deployment
```bash
# Deploy service to Railway
railway up

# Set environment variables in Railway dashboard:
# - AMBER_API_KEY
# - DATABASE_URL (auto-configured for Railway Postgres)
# - HISTORICAL_START_DATE
```

## Database Schema

The service creates and manages these PostgreSQL tables:

### Sites
- `id`: Site identifier (VARCHAR, PRIMARY KEY)
- `nmi`: National Metering Identifier (VARCHAR)

### Price Data
- `site_id`: Reference to site (FOREIGN KEY)
- `nem_time`: NEM timestamp (TIMESTAMP WITH TIME ZONE)
- `channel_type`: Energy channel type (VARCHAR)
- `per_kwh`: Price per kWh in cents (DECIMAL)
- `spot_per_kwh`: NEM spot price (DECIMAL)
- `renewables`: Renewable percentage (DECIMAL)
- Additional API fields: `start_time`, `end_time`, `duration`, `spike_status`, etc.

### Usage Data
- `site_id`: Reference to site (FOREIGN KEY)
- `nem_time`: NEM timestamp (TIMESTAMP WITH TIME ZONE)
- `channel_id`: Channel identifier (E1, B1, etc.)
- `channel_type`: Energy channel type (VARCHAR)
- `kwh`: Energy consumed/generated (DECIMAL)
- `cost`: Cost in cents (DECIMAL)
- `quality`: Data quality indicator (VARCHAR)
- Additional API fields: `start_time`, `end_time`, `duration`, etc.

## Monitoring

### Health Checks
- Database connectivity validation
- API client initialization
- Schema creation verification

### Logging
- Structured logging with timestamps
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Collection progress tracking
- Error reporting with context

### Metrics
- Sites collected count
- Price/usage record counts
- Collection cycle timing
- API rate limit tracking

## API Integration

Uses Amber Electric API v2.0.12 with:
- Automatic retry on rate limit hits
- 7-day maximum date range chunks
- Raw data structure preservation
- Handle for `actual_instance` wrapper objects