# Amber-Home 🏠⚡

Energy data collection and analysis platform for Amber Electric customers.

## What is Amber-Home?

Amber-Home is a backend platform that automatically collects, stores, and analyzes your Amber Electric energy data using a microservices architecture.

## Architecture

### Backend Services
- **Data Collector Service**: Automated data collection from Amber Electric API
- **Dashboard Application**: Streamlit web interface for data visualization  
- **Query Tools**: CLI utilities for data analysis

### Tech Stack
- Python 3.12 with uv dependency management
- PostgreSQL database
- Docker containerization
- Railway deployment ready

## Quick Start

### 1. Data Collection Service

```bash
# Navigate to data collector service
cd services/datacollector-service

# Copy environment template
cp .env.example .env.local

# Configure your settings
# Add AMBER_API_KEY, DATABASE_URL, HISTORICAL_START_DATE

# Run locally
uv sync
uv run python main.py

# Or run with Docker
docker-compose up -d
```

### 2. Dashboard & Analysis

```bash
# From project root
# Launch Streamlit dashboard
uv run streamlit run dashboard.py

# Query your data
python query_data.py --summary
python query_data.py --costs 7
python query_data.py --prices 14
```

## Backend Services

### Data Collector Service
Located in `services/datacollector-service/`

**Features:**
- Historical data initialization from configurable start date
- Continuous 5-minute data collection cycles
- Separate price and usage data tracking (handles data misalignment)
- Raw API data storage with no filtering
- Robust error handling and rate limiting
- PostgreSQL integration with Railway deployment support

**Configuration:**
```bash
AMBER_API_KEY=your_amber_api_key_here
DATABASE_URL=postgresql://user:pass@host:port/dbname  
HISTORICAL_START_DATE=2024-01-01
COLLECTION_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

### Future Services
Planned backend services:
- **API Service**: REST API for frontend applications
- **Analytics Service**: Data processing and analytics engine
- **Notification Service**: Alerts and messaging system
- **Export Service**: Data export and reporting functionality

## Database Schema (PostgreSQL)

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
- Enhanced fields: `start_time`, `end_time`, `duration`, `spike_status`, etc.

### Usage Data
- `site_id`: Reference to site (FOREIGN KEY)
- `nem_time`: NEM timestamp (TIMESTAMP WITH TIME ZONE)
- `channel_id`: Channel identifier (E1, B1, etc.)
- `channel_type`: Energy channel type (VARCHAR)
- `kwh`: Energy consumed/generated (DECIMAL)
- `cost`: Cost in cents (DECIMAL)
- `quality`: Data quality indicator (VARCHAR)
- Enhanced fields: `start_time`, `end_time`, `duration`, etc.

## Deployment

### Railway Platform
Each service can be deployed independently:

```bash
cd services/datacollector-service
railway up
```

Configure environment variables in Railway dashboard:
- `AMBER_API_KEY`
- `DATABASE_URL` (auto-configured for Railway Postgres)
- `HISTORICAL_START_DATE`

### Local Development
```bash
# Run data collection service
cd services/datacollector-service
uv run python main.py

# Run dashboard (from project root)
uv run streamlit run dashboard.py
```

## Analysis Examples

### Cost Analysis
```bash
# View cost breakdown for last 7 days
python query_data.py --costs 7

# Monthly cost summary
python query_data.py --sql "
    SELECT 
        DATE_TRUNC('month', nem_time) as month,
        SUM(CASE WHEN cost > 0 THEN cost/100 ELSE 0 END) as total_cost
    FROM usage_data 
    GROUP BY month 
    ORDER BY month DESC
"
```

### Price Analysis
```bash
# Price trends for last 14 days
python query_data.py --prices 14

# Peak vs off-peak pricing
python query_data.py --sql "
    SELECT 
        EXTRACT(hour FROM nem_time) as hour,
        AVG(per_kwh) as avg_price_cents
    FROM price_data 
    GROUP BY hour 
    ORDER BY hour
"
```

### Solar Analysis
```bash
# Solar generation vs consumption
python query_data.py --sql "
    SELECT 
        DATE(nem_time) as date,
        SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as consumed,
        SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as generated
    FROM usage_data 
    WHERE channel_id IN ('E1', 'B1')
    GROUP BY date 
    ORDER BY date DESC
"
```

## Project Structure

```
amber-home/
├── services/
│   └── datacollector-service/     # Data collection microservice
│       ├── app/                   # Application code
│       ├── Dockerfile            # Container definition
│       ├── docker-compose.yml    # Service orchestration
│       └── README.md             # Service documentation
├── dashboard.py                  # Streamlit dashboard
├── query_data.py                # CLI analysis tool
├── CLAUDE.md                     # Development documentation
└── README.md                     # This file
```

## Contributing

When adding new services:
1. Create service directory under `services/`
2. Follow the datacollector-service structure  
3. Include comprehensive README.md
4. Add Docker configuration
5. Update main project documentation

## Tips

- **Data Collection**: The service handles all data collection automatically
- **API Limits**: Respects Amber API limits (50 calls per 5 minutes, 7-day max ranges)  
- **Data Integrity**: Raw API data storage preserves all original information
- **Monitoring**: Use Docker logs to monitor collection progress
- **Backup**: PostgreSQL database contains all your valuable energy data

---

**Amber-Home** gives you complete control over your energy data with a scalable, microservices architecture! 🏠⚡📊