import React from 'react';

interface MetricCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaType?: 'positive' | 'negative' | 'neutral';
  help?: string;
}

export default function MetricCard({ label, value, delta, deltaType = 'neutral', help }: MetricCardProps) {
  const getDeltaColor = () => {
    switch (deltaType) {
      case 'positive':
        return 'text-green-600';
      case 'negative':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
      <div className="flex flex-col">
        <div className="text-sm font-medium text-gray-600 mb-1">
          {label}
          {help && (
            <span className="ml-1 text-xs text-gray-400" title={help}>
              ⓘ
            </span>
          )}
        </div>
        <div className="text-2xl font-bold text-gray-900 mb-1">
          {value}
        </div>
        {delta && (
          <div className={`text-sm ${getDeltaColor()}`}>
            {delta}
          </div>
        )}
      </div>
    </div>
  );
}