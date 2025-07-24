import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

export async function GET() {
  try {
    const query = `
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

    const result = await pool.query(query);
    return NextResponse.json(result.rows);
  } catch (error) {
    console.error('Error fetching price data:', error);
    return NextResponse.json({ error: 'Failed to fetch price data' }, { status: 500 });
  }
}