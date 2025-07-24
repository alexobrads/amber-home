'use client';

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { CombinedPriceData } from '@/lib/database';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler,
  annotationPlugin
);

interface CombinedPriceChartProps {
  data: CombinedPriceData;
}

export default function CombinedPriceChart({ data }: CombinedPriceChartProps) {
  if ((!data.historical || data.historical.length === 0) && (!data.forecast || data.forecast.length === 0)) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No price data available</p>
      </div>
    );
  }

  const datasets = [];

  // Historical data
  if (data.historical && data.historical.length > 0) {
    const historicalImport = data.historical.filter(item => item.channel_type.includes('GENERAL'));
    const historicalExport = data.historical.filter(item => item.channel_type.includes('FEEDIN'));

    if (historicalImport.length > 0) {
      datasets.push({
        label: 'Historical Import',
        data: historicalImport.map(item => ({
          x: item.aest_time,
          y: item.per_kwh
        })),
        borderColor: '#ff6b6b',
        backgroundColor: '#ff6b6b',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHitRadius: 10,
        borderWidth: 3,
      });
    }

    if (historicalExport.length > 0) {
      datasets.push({
        label: 'Historical Export',
        data: historicalExport.map(item => ({
          x: item.aest_time,
          y: item.per_kwh * -1
        })),
        borderColor: '#4ecdc4',
        backgroundColor: '#4ecdc4',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHitRadius: 10,
        borderWidth: 3,
      });
    }
  }

  // Forecast data
  if (data.forecast && data.forecast.length > 0) {
    const forecastImport = data.forecast.filter(item => item.channel_type.includes('GENERAL'));
    const forecastExport = data.forecast.filter(item => item.channel_type.includes('FEEDIN'));

    if (forecastImport.length > 0) {
      datasets.push({
        label: 'Forecast Import',
        data: forecastImport.map(item => ({
          x: item.aest_time,
          y: item.per_kwh
        })),
        borderColor: '#ff6b6b',
        backgroundColor: '#ff6b6b',
        borderDash: [5, 5],
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHitRadius: 10,
      });

      // Add uncertainty bands if available
      if (forecastImport.some(item => item.advanced_price_high && item.advanced_price_low)) {
        // Add high bound (invisible line for fill reference)
        datasets.push({
          label: 'Import High',
          data: forecastImport.map(item => ({
            x: item.aest_time,
            y: item.advanced_price_high
          })),
          borderColor: 'rgba(255, 107, 107, 0)',
          backgroundColor: 'rgba(255, 107, 107, 0)',
          fill: false,
          pointRadius: 0,
        });

        // Add uncertainty band (fills between high and low)
        datasets.push({
          label: 'Import Uncertainty',
          data: forecastImport.map(item => ({
            x: item.aest_time,
            y: item.advanced_price_low
          })),
          borderColor: 'rgba(255, 107, 107, 0)',
          backgroundColor: 'rgba(255, 107, 107, 0.2)',
          fill: '-1',
          pointRadius: 0,
        });
      }
    }

    if (forecastExport.length > 0) {
      datasets.push({
        label: 'Forecast Export',
        data: forecastExport.map(item => ({
          x: item.aest_time,
          y: item.per_kwh * -1
        })),
        borderColor: '#4ecdc4',
        backgroundColor: '#4ecdc4',
        borderDash: [5, 5],
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHitRadius: 10,
      });

      // Add uncertainty bands if available
      if (forecastExport.some(item => item.advanced_price_high && item.advanced_price_low)) {
        // Add high bound (invisible line for fill reference)
        datasets.push({
          label: 'Export High',
          data: forecastExport.map(item => ({
            x: item.aest_time,
            y: (item.advanced_price_high || 0) * -1
          })),
          borderColor: 'rgba(78, 205, 196, 0)',
          backgroundColor: 'rgba(78, 205, 196, 0)',
          fill: false,
          pointRadius: 0,
        });

        // Add uncertainty band (fills between high and low)
        datasets.push({
          label: 'Export Uncertainty',
          data: forecastExport.map(item => ({
            x: item.aest_time,
            y: (item.advanced_price_low || 0) * -1
          })),
          borderColor: 'rgba(78, 205, 196, 0)',
          backgroundColor: 'rgba(78, 205, 196, 0.2)',
          fill: '-1',
          pointRadius: 0,
        });
      }
    }
  }

  const chartData = { datasets };

  const options = {
    responsive: true,
    plugins: {
      // Add background zones for price brackets
      annotation: {
        annotations: {
          greenZone: {
            type: 'box',
            yMin: 0,
            yMax: 20,
            backgroundColor: 'rgba(34, 197, 94, 0.2)', // Green - good prices
            borderWidth: 0,
          },
          yellowGreenZone: {
            type: 'box',
            yMin: 20,
            yMax: 30,
            backgroundColor: 'rgba(132, 204, 22, 0.2)', // Yellow-green transition
            borderWidth: 0,
          },
          yellowZone: {
            type: 'box', 
            yMin: 30,
            yMax: 40,
            backgroundColor: 'rgba(234, 179, 8, 0.2)', // Yellow - moderate prices
            borderWidth: 0,
          },
          orangeZone: {
            type: 'box',
            yMin: 40,
            yMax: 50,
            backgroundColor: 'rgba(249, 115, 22, 0.2)', // Orange - higher prices
            borderWidth: 0,
          },
          redOrangeZone: {
            type: 'box',
            yMin: 50,
            yMax: 60,
            backgroundColor: 'rgba(255, 87, 51, 0.2)', // Red-orange transition
            borderWidth: 0,
          },
          redZone: {
            type: 'box',
            yMin: 60,
            yMax: 70,
            backgroundColor: 'rgba(239, 68, 68, 0.2)', // Red - expensive prices
            borderWidth: 0,
          },
          darkRedZone: {
            type: 'box',
            yMin: 70,
            yMax: 80,
            backgroundColor: 'rgba(220, 38, 38, 0.2)', // Dark red - very expensive
            borderWidth: 0,
          },
          veryDarkRedZone: {
            type: 'box',
            yMin: 80,
            yMax: 100,
            backgroundColor: 'rgba(185, 28, 28, 0.2)', // Very dark red - extremely expensive
            borderWidth: 0,
          }
        }
      },
      legend: {
        position: 'top' as const,
        labels: {
          filter: function(legendItem: any) {
            // Hide high bounds from legend, keep uncertainty bands
            return legendItem.text !== 'Import High' && legendItem.text !== 'Export High';
          }
        }
      },
      title: {
        display: true,
        text: 'Electricity Prices - Historical + 10h Forecasts',
        font: {
          size: 20,
          color: '#2c3e50'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}¢/kWh`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            hour: 'HH:mm',
            day: 'MM/dd'
          }
        },
        title: {
          display: true,
          text: 'Time (AEST)'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Price (¢/kWh)'
        },
        ticks: {
          stepSize: 10,
          callback: function(value: any) {
            return value + '¢';
          }
        },
        grid: {
          color: function(context: any) {
            return '#374151';
          },
          lineWidth: function(context: any) {
            if (context.tick.value === 0 || context.tick.value === 10 || context.tick.value === 20) {
              return 2; // Thicker lines for key values
            }
            return 1; // Default line width
          }
        }
      }
    },
    maintainAspectRatio: false
  };

  return (
    <div className="h-96">
      <Line data={chartData} options={options} />
    </div>
  );
}