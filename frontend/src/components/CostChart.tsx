'use client';

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { CostStats } from '@/lib/database';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface CostChartProps {
  data: CostStats;
  type: 'cost' | 'usage';
}

export default function CostChart({ data, type }: CostChartProps) {
  if (!data.daily_data || data.daily_data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No daily {type} data available</p>
      </div>
    );
  }

  const labels = data.daily_data.map(item => item.date);

  const chartData = type === 'cost' ? {
    labels,
    datasets: [
      {
        type: 'bar' as const,
        label: 'Import Cost',
        data: data.daily_data.map(item => item.daily_cost_import),
        backgroundColor: '#ff6b6b',
        borderColor: '#ff6b6b',
      },
      {
        type: 'bar' as const,
        label: 'Export Credit',
        data: data.daily_data.map(item => -item.daily_cost_export),
        backgroundColor: '#4ecdc4',
        borderColor: '#4ecdc4',
      },
      {
        type: 'line' as const,
        label: 'Net Cost',
        data: data.daily_data.map(item => item.daily_cost_net),
        borderColor: '#2c3e50',
        backgroundColor: '#2c3e50',
        borderWidth: 3,
        pointRadius: 8,
        tension: 0.1,
      },
    ],
  } : {
    labels,
    datasets: [
      {
        type: 'bar' as const,
        label: 'Import (kWh)',
        data: data.daily_data.map(item => item.daily_kwh_import),
        backgroundColor: '#ff6b6b',
        borderColor: '#ff6b6b',
      },
      {
        type: 'bar' as const,
        label: 'Export (kWh)',
        data: data.daily_data.map(item => -item.daily_kwh_export),
        backgroundColor: '#4ecdc4',
        borderColor: '#4ecdc4',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: type === 'cost' ? 'Daily Cost Breakdown - Past 7 Days' : 'Daily Usage Breakdown - Past 7 Days',
        font: {
          size: 20,
          color: '#2c3e50'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const suffix = type === 'cost' ? '' : ' kWh';
            const prefix = type === 'cost' ? '$' : '';
            return `${context.dataset.label}: ${prefix}${Math.abs(context.parsed.y).toFixed(2)}${suffix}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        title: {
          display: true,
          text: type === 'cost' ? 'Cost ($)' : 'Usage (kWh)'
        },
        beginAtZero: true
      }
    },
    maintainAspectRatio: false
  };

  return (
    <div className="h-96">
      <Chart data={chartData} options={options} />
    </div>
  );
}