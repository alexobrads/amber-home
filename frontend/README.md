# Amber-Home Frontend

A simple Streamlit frontend application for visualizing energy data from the Amber Electric platform.

## Features

- **Price Charts**: Real-time electricity prices for import and export over the past 24 hours (displayed in AEST)
- **Usage Charts**: Energy consumption and generation over the past 24 hours (displayed in AEST)
- **Cost Statistics**: Weekly cost breakdown and energy usage statistics
- **Auto-refresh**: Data refreshes every 5 minutes (configurable)
- **Responsive Design**: Clean, modern interface optimized for energy monitoring

## Quick Start

### Local Development

1. **Set up environment**:
   ```bash
   cd frontend
   cp .env.example .env
   # Edit .env with your database connection details
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the application**:
   ```bash
   uv run streamlit run app/main.py
   ```

4. **Access the dashboard**:
   - Open your browser to `http://localhost:8501`

### Docker Deployment

1. **Run with Docker Compose**:
   ```bash
   cd frontend
   docker-compose up -d
   ```

2. **Access the dashboard**:
   - Open your browser to `http://localhost:8501`

3. **Stop the service**:
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
- `AUTO_REFRESH_SECONDS`: Data refresh interval in seconds (default: 300)

### Database Requirements

The frontend connects to the same PostgreSQL database used by the data collector service. Ensure:

1. **Database is running** and accessible
2. **Data collector service** has populated the database with price and usage data
3. **Connection details** are correct in your environment configuration

## Data Visualization

### Price Charts
- **Import Prices**: Shows E1 (GENERAL) channel pricing
- **Export Prices**: Shows B1 (FEED_IN) channel pricing
- **Time Range**: Past 24 hours in Australian Eastern Standard Time
- **Metrics**: Current, average, min/max prices

### Usage Charts
- **Import Usage**: Energy consumption (positive values)
- **Export Usage**: Energy generation (negative values for visual distinction)
- **Time Range**: Past 24 hours in Australian Eastern Standard Time
- **Metrics**: Total import/export, net usage, costs

### Cost Statistics
- **Weekly Summary**: Total costs, daily averages, import vs export breakdown
- **Energy Metrics**: Total kWh imported/exported, net usage
- **Daily Breakdown**: Individual day costs and usage over the past week
- **Trends**: Visual charts showing daily cost and usage patterns

## Architecture

### Application Structure
```
frontend/
├── app/
│   ├── main.py              # Main Streamlit application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database service layer
│   └── components/          # UI components
│       ├── price_charts.py  # Price visualization
│       ├── usage_charts.py  # Usage visualization
│       └── cost_stats.py    # Cost statistics
├── pyproject.toml          # Dependencies
├── Dockerfile              # Container definition
├── docker-compose.yml      # Service orchestration
└── README.md              # This file
```

### Key Components

- **DatabaseService**: Handles PostgreSQL connections and data queries
- **Price Charts**: Interactive price visualization with Plotly
- **Usage Charts**: Energy consumption/generation visualization
- **Cost Statistics**: Weekly cost analysis and breakdowns
- **Auto-refresh**: Cached data with configurable refresh intervals

## Development

### Adding New Features

1. **New visualizations**: Add components to `app/components/`
2. **Database queries**: Extend `DatabaseService` in `app/database.py`
3. **Configuration**: Add new settings to `app/config.py`
4. **UI updates**: Modify `app/main.py` for layout changes

### Testing

```bash
# Run the application locally
uv run streamlit run app/main.py

# Test with Docker
docker-compose up --build

# Check logs
docker-compose logs -f frontend
```

## Deployment

### Railway Platform

1. **Deploy to Railway**:
   ```bash
   cd frontend
   railway up
   ```

2. **Set environment variables** in Railway dashboard:
   - `DATABASE_URL` (connects to your PostgreSQL database - Railway auto-configures this)
   - `AUTO_REFRESH_SECONDS` (optional, default: 300)

3. **Railway will automatically**:
   - Detect the Dockerfile and build the container
   - Expose the service on port 8501
   - Set up the DATABASE_URL environment variable
   - Provide a public URL for your dashboard

4. **Access your deployment** via the Railway-provided URL

### Local Development with Docker

```bash
# Build and run the frontend
cd frontend
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Stop the service
docker-compose down
```

### Production Considerations

- **Database Connection**: Automatically uses Railway's PostgreSQL connection
- **Caching**: Data refreshes every 5 minutes (configurable via AUTO_REFRESH_SECONDS)
- **Security**: All credentials managed via Railway environment variables
- **Performance**: Streamlit caching enabled for optimal performance
- **Scaling**: Railway handles auto-scaling based on usage

## Troubleshooting

### Common Issues

1. **No data available**: 
   - Check that the data collector service is running
   - Verify database connection details
   - Ensure data has been collected (check database tables)

2. **Connection errors**:
   - Verify `DATABASE_URL` is correct
   - Check that PostgreSQL is running and accessible
   - Ensure firewall/network settings allow connections

3. **Charts not displaying**:
   - Check browser console for JavaScript errors
   - Verify data is being returned from database queries
   - Check Streamlit logs for errors

### Logs

```bash
# View application logs
docker-compose logs -f frontend

# View database logs
docker-compose logs -f postgres
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Verify your database contains the expected data structure
4. Ensure the data collector service is running and populating data