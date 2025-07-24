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
          DATE(nem_time AT TIME ZONE 'Australia/Sydney') as date,
          SUM(CASE WHEN cost > 0 THEN cost/100 ELSE 0 END) as daily_cost_import,
          SUM(CASE WHEN cost < 0 THEN ABS(cost)/100 ELSE 0 END) as daily_cost_export,
          SUM(cost/100) as daily_cost_net,
          SUM(CASE WHEN kwh > 0 THEN kwh ELSE 0 END) as daily_kwh_import,
          SUM(CASE WHEN kwh < 0 THEN ABS(kwh) ELSE 0 END) as daily_kwh_export,
          COUNT(*) as record_count
      FROM usage_data 
      WHERE nem_time AT TIME ZONE 'Australia/Sydney' >= 
            (CURRENT_DATE AT TIME ZONE 'Australia/Sydney')::date - INTERVAL '7 days'
      GROUP BY DATE(nem_time AT TIME ZONE 'Australia/Sydney')
      ORDER BY date DESC
    `;

    const result = await pool.query(query);
    
    if (result.rows.length === 0) {
      return NextResponse.json({
        total_cost: 0,
        avg_daily_cost: 0,
        total_import_cost: 0,
        total_export_cost: 0,
        total_kwh_import: 0,
        total_kwh_export: 0,
        days_with_data: 0,
        daily_data: []
      });
    }

    const dailyData = result.rows;
    const totalCost = dailyData.reduce((sum, day) => sum + parseFloat(day.daily_cost_net), 0);
    const totalImportCost = dailyData.reduce((sum, day) => sum + parseFloat(day.daily_cost_import), 0);
    const totalExportCost = dailyData.reduce((sum, day) => sum + parseFloat(day.daily_cost_export), 0);
    const totalKwhImport = dailyData.reduce((sum, day) => sum + parseFloat(day.daily_kwh_import), 0);
    const totalKwhExport = dailyData.reduce((sum, day) => sum + parseFloat(day.daily_kwh_export), 0);

    return NextResponse.json({
      total_cost: totalCost,
      avg_daily_cost: totalCost / dailyData.length,
      total_import_cost: totalImportCost,
      total_export_cost: totalExportCost,
      total_kwh_import: totalKwhImport,
      total_kwh_export: totalKwhExport,
      days_with_data: dailyData.length,
      daily_data: dailyData
    });
  } catch (error) {
    console.error('Error fetching cost stats:', error);
    return NextResponse.json({ error: 'Failed to fetch cost stats' }, { status: 500 });
  }
}