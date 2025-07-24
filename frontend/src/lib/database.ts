/**
 * Database service for Amber-Home Frontend Application.
 */

export interface PriceData {
  aest_time: string;
  channel_type: string;
  per_kwh: number;
  spot_per_kwh: number;
  renewables: number;
  descriptor: string;
  spike_status: string;
}

export interface UsageData {
  aest_time: string;
  channel_id: string;
  channel_type: string;
  kwh: number;
  cost: number;
  quality: string;
}

export interface CostStats {
  total_cost: number;
  avg_daily_cost: number;
  total_import_cost: number;
  total_export_cost: number;
  total_kwh_import: number;
  total_kwh_export: number;
  days_with_data: number;
  daily_data: DailyData[];
}

export interface DailyData {
  date: string;
  daily_cost_import: number;
  daily_cost_export: number;
  daily_cost_net: number;
  daily_kwh_import: number;
  daily_kwh_export: number;
  record_count: number;
}

export interface ForecastData {
  aest_time: string;
  channel_type: string;
  per_kwh: number;
  spot_per_kwh: number;
  renewables: number;
  descriptor: string;
  spike_status: string;
  forecast_type: string;
  advanced_price_low: number;
  advanced_price_predicted: number;
  advanced_price_high: number;
  range_low: number;
  range_high: number;
}

export interface CombinedPriceData {
  historical: PriceData[];
  forecast: ForecastData[];
}