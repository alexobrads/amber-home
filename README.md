# Amber-Home 🏠⚡

Simple home energy data collection and analysis for Amber Electric customers.

## What is Amber-Home?

Amber-Home is a lightweight tool to collect, store, and analyze your Amber Electric energy data. It uses a functional approach with simple Python scripts and DuckDB for fast analytics.

## Features

- **📊 Data Collection**: Automated collection of prices, usage, and renewable data
- **🗄️ Local Storage**: DuckDB database for fast analytical queries  
- **📈 Simple Analysis**: Built-in cost analysis and price trend tools
- **🐳 Docker Ready**: Containerized DuckDB for easy deployment
- **📱 Dashboard**: Streamlit dashboard for visual analysis

## Quick Start

### 1. Setup

```bash
# Clone and setup
git clone <repo-url> amber-home
cd amber-home

# Copy environment file and add your API key
cp .env.example .env
nano .env  # Add your AMBER_API_KEY

# Start DuckDB container
docker-compose up -d

# Install Python dependencies
uv sync  # or pip install -r requirements.txt
```

### 2. Collect Your Data

```bash
# First, collect your sites
python collect_data.py --type sites

# Collect recent price data (last 30 days)
python collect_data.py --type prices --start 2024-06-01 --end 2024-06-30

# Collect recent usage data
python collect_data.py --type usage --start 2024-06-01 --end 2024-06-30

# Check what you've collected
python query_data.py --summary
```

### 3. Analyze Your Data

```bash
# View cost analysis for last 7 days
python query_data.py --costs 7

# View price trends for last 14 days  
python query_data.py --prices 14

# Run custom SQL queries
python query_data.py --sql "SELECT AVG(per_kwh) FROM price_data WHERE date >= '2024-06-01'"
```

### 4. Visual Dashboard

```bash
# Launch Streamlit dashboard
uv run streamlit run dashboard.py
```

## Usage Examples

### Collect Historical Data

```bash
# Collect all data for 2024
python collect_data.py --type prices --start 2024-01-01 --end 2024-12-31
python collect_data.py --type usage --start 2024-01-01 --end 2024-12-31

# Collect data for specific site
python collect_data.py --type usage --site YOUR_SITE_ID --start 2024-06-01 --end 2024-06-30
```

### Analyze Your Energy Patterns

```bash
# Cost breakdown for last month
python query_data.py --costs 30

# Price volatility analysis
python query_data.py --prices 30

# Custom analysis
python query_data.py --sql "
    SELECT 
        DATE_TRUNC('month', date) as month,
        SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as consumption_kwh,
        SUM(cost_dollars) as total_cost
    FROM usage_data 
    GROUP BY month 
    ORDER BY month
"
```

### Query Your Data Directly

```bash
# Connect to DuckDB directly
docker-compose exec duckdb python -c "
import duckdb
conn = duckdb.connect('/data/amber.duckdb')
print(conn.execute('SELECT COUNT(*) FROM price_data').fetchone())
"

# Export data to CSV
python query_data.py --sql "SELECT * FROM usage_data" > my_usage.csv
```

## Database Schema

### Sites
- `id` - Amber site identifier
- `nmi` - National Meter Identifier  
- `network` - Distribution network

### Price Data
- `site_id` - Site identifier
- `nem_time` - NEM timestamp
- `channel_type` - General/ControlledLoad/FeedIn
- `per_kwh` - Your price (cents/kWh)
- `spot_per_kwh` - Wholesale price (cents/kWh)
- `renewables` - Grid renewable percentage
- `date` - Date for easy querying

### Usage Data  
- `site_id` - Site identifier
- `nem_time` - NEM timestamp
- `channel_id` - Channel identifier (E1, B1, etc.)
- `kwh` - Energy consumed/generated
- `cost_dollars` - Cost in dollars (converted from cents)
- `quality` - Data quality (billable/estimated)
- `date` - Date for easy querying

## Useful SQL Queries

```sql
-- Daily cost summary
SELECT 
    date,
    SUM(CASE WHEN cost_dollars > 0 THEN cost_dollars ELSE 0 END) as daily_cost,
    SUM(CASE WHEN cost_dollars < 0 THEN ABS(cost_dollars) ELSE 0 END) as daily_credit
FROM usage_data 
GROUP BY date 
ORDER BY date DESC;

-- Peak vs off-peak price analysis
SELECT 
    EXTRACT(hour FROM nem_time) as hour,
    AVG(per_kwh) as avg_price,
    COUNT(*) as intervals
FROM price_data 
GROUP BY hour 
ORDER BY hour;

-- Solar generation vs consumption
SELECT 
    date,
    SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as consumed,
    SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as generated
FROM usage_data 
WHERE channel_id IN ('E1', 'B1')  -- Adjust for your channels
GROUP BY date 
ORDER BY date DESC;
```

## File Structure

```
amber-home/
├── docker-compose.yml      # DuckDB container
├── collect_data.py        # Data collection script
├── query_data.py          # Query and analysis tool
├── dashboard.py           # Streamlit dashboard
├── amber_client.py        # Amber API client
├── schema.sql             # Database schema
├── .env.example           # Environment template
└── data/                  # Database storage
    └── amber.duckdb       # Your energy data
```

## Tips

- **Start Small**: Collect a few days of data first to test everything works
- **Historical Data**: The Amber API limits historical requests to 7-day chunks
- **Rate Limits**: Be respectful of API limits - the scripts include delays
- **Backup**: Your `data/amber.duckdb` file contains all your data - back it up!
- **Analysis**: DuckDB is excellent for time-series analysis - explore the SQL capabilities

## Troubleshooting

**Database not found**: Run `python collect_data.py --type sites` first

**API errors**: Check your `AMBER_API_KEY` in `.env` file

**No data**: Verify your site ID with `python query_data.py --summary`

**Container issues**: `docker-compose down && docker-compose up -d`

---

**Amber-Home** gives you complete control over your energy data. Collect it, analyze it, and optimize your energy usage! 🏠⚡📊