# Amber-Home Backend Services

This directory contains the backend microservices for the Amber-Home energy data platform.

## Services Overview

### datacollector-service
A containerized data collection service that automatically gathers energy data from the Amber Electric API.

**Key Features:**
- Historical data initialization from configurable start date
- Continuous 5-minute data collection cycles
- Separate price and usage data tracking (handles data misalignment)
- Raw API data storage with no filtering
- Robust error handling and rate limiting
- PostgreSQL integration with Railway deployment support

**Tech Stack:**
- Python 3.12 with uv dependency management
- PostgreSQL database
- Docker containerization
- Amber Electric API v2.0.12 integration

## Architecture

```
services/
├── datacollector-service/     # Data collection microservice
│   ├── app/                   # Application code
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Service orchestration
│   └── README.md             # Service documentation
└── README.md                 # This file
```

## Service Communication

Services communicate through:
- **Shared Database**: PostgreSQL database for data storage
- **Environment Variables**: Configuration and service discovery
- **Docker Networking**: Container-to-container communication (future)

## Development

### Prerequisites
- Python 3.12+
- uv package manager
- Docker and Docker Compose
- PostgreSQL (local or Railway)

### Setup
```bash
# Clone repository
git clone <repo-url>
cd amber-home

# Navigate to specific service
cd services/datacollector-service

# Install dependencies
uv sync

# Run service
uv run python main.py
```

### Docker Development
```bash
# Build and run all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Deployment

### Railway Platform
Each service can be deployed independently to Railway:

```bash
cd services/datacollector-service
railway up
```

Configure environment variables in Railway dashboard:
- `AMBER_API_KEY`
- `DATABASE_URL` (auto-configured for Railway Postgres)
- `HISTORICAL_START_DATE`

### Environment Configuration
Services use environment variables for configuration:

**Required:**
- `AMBER_API_KEY`: Amber Electric API key
- `DATABASE_URL`: PostgreSQL connection string
- `HISTORICAL_START_DATE`: Start date for data collection

**Optional:**
- `COLLECTION_INTERVAL_MINUTES`: Collection frequency (default: 5)
- `LOG_LEVEL`: Logging level (default: INFO)
- `FORCE_REINIT`: Force data re-collection (default: false)

## Future Services

Planned backend services:
- **api-service**: REST API for frontend applications
- **analytics-service**: Data processing and analytics engine
- **notification-service**: Alerts and messaging system
- **export-service**: Data export and reporting functionality

## Contributing

When adding new services:
1. Create service directory under `services/`
2. Follow the datacollector-service structure
3. Include comprehensive README.md
4. Add Docker configuration
5. Update this overview documentation