import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

export async function GET() {
  try {
    // Historical data query
    const historicalQuery = `
      SELECT 
          nem_time AT TIME ZONE 'Australia/Sydney' as aest_time,
          channel_type,
          per_kwh,
          spot_per_kwh,
          renewables,
          descriptor,
          spike_status
      FROM price_data 
      WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
            (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date
        AND nem_time AT TIME ZONE 'Australia/Sydney' <= 
            NOW() AT TIME ZONE 'Australia/Sydney'
      ORDER BY nem_time ASC
    `;

    // Forecast data query
    const forecastQuery = `
      SELECT 
          nem_time AT TIME ZONE 'Australia/Sydney' as aest_time,
          channel_type,
          per_kwh,
          spot_per_kwh,
          renewables,
          descriptor,
          spike_status,
          forecast_type,
          advanced_price_low,
          advanced_price_predicted,
          advanced_price_high,
          range_low,
          range_high
      FROM price_forecasts 
      WHERE nem_time AT TIME ZONE 'Australia/Sydney' > 
            NOW() AT TIME ZONE 'Australia/Sydney'
        AND nem_time AT TIME ZONE 'Australia/Sydney' <= 
            NOW() AT TIME ZONE 'Australia/Sydney' + INTERVAL '10 hours'
        AND forecast_generated_at = (
            SELECT MAX(forecast_generated_at) 
            FROM price_forecasts 
            WHERE forecast_generated_at >= NOW() - INTERVAL '2 hours'
        )
      ORDER BY nem_time ASC
    `;

    const [historicalResult, forecastResult] = await Promise.all([
      pool.query(historicalQuery),
      pool.query(forecastQuery)
    ]);

    return NextResponse.json({
      historical: historicalResult.rows,
      forecast: forecastResult.rows
    });
  } catch (error) {
    console.error('Error fetching combined price data:', error);
    return NextResponse.json({
      historical: [],
      forecast: [],
      error: 'Failed to fetch combined price data'
    }, { status: 500 });
  }
}