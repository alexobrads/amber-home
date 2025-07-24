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
import { UsageData } from '@/lib/database';

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

interface UsageChartProps {
  data: UsageData[];
}

export default function UsageChart({ data }: UsageChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No usage data available</p>
      </div>
    );
  }

  // Separate import and export data
  const importData = data.filter(item => item.kwh > 0);
  const exportData = data.filter(item => item.kwh < 0);

  const chartData = {
    datasets: [
      {
        label: 'Import Usage (E1)',
        data: importData.map(item => ({
          x: item.aest_time,
          y: item.kwh
        })),
        borderColor: '#ff6b6b',
        backgroundColor: 'rgba(255, 107, 107, 0.3)',
        fill: 'origin',
        tension: 0.1,
      },
      {
        label: 'Export Usage (B1)',
        data: exportData.map(item => ({
          x: item.aest_time,
          y: item.kwh
        })),
        borderColor: '#4ecdc4',
        backgroundColor: 'rgba(78, 205, 196, 0.3)',
        fill: 'origin',
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
        text: 'Energy Usage - Past 24 Hours',
        font: {
          size: 20,
          color: '#2c3e50'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(3)} kWh`;
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
          text: 'Usage (kWh)'
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