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
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { PriceData } from '@/lib/database';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
);

interface PriceChartProps {
  data: PriceData[];
}

export default function PriceChart({ data }: PriceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No price data available</p>
      </div>
    );
  }

  // Separate import and export data
  const importData = data.filter(item => item.channel_type.includes('GENERAL'));
  const exportData = data.filter(item => item.channel_type.includes('FEEDIN'));

  const chartData = {
    datasets: [
      {
        label: 'Import Price (E1)',
        data: importData.map(item => ({
          x: item.aest_time,
          y: item.per_kwh
        })),
        borderColor: '#ff6b6b',
        backgroundColor: '#ff6b6b',
        tension: 0.1,
      },
      {
        label: 'Export Price (B1)',
        data: exportData.map(item => ({
          x: item.aest_time,
          y: item.per_kwh
        })),
        borderColor: '#4ecdc4',
        backgroundColor: '#4ecdc4',
        tension: 0.1,
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
        text: 'Electricity Prices - Past 24 Hours',
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