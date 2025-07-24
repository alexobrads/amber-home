'use client';

import React, { useEffect, useState } from 'react';
import CombinedPriceChart from '@/components/CombinedPriceChart';
import { CombinedPriceData } from '@/lib/database';

export default function Home() {
  const [combinedPriceData, setCombinedPriceData] = useState<CombinedPriceData>({ historical: [], forecast: [] });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const combinedRes = await fetch('/api/combined-price-data');

      if (combinedRes.ok) {
        const combinedData = await combinedRes.json();
        setCombinedPriceData(combinedData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const calculatePriceSummary = () => {
    if (!combinedPriceData.historical || combinedPriceData.historical.length === 0) return null;

    const importData = combinedPriceData.historical.filter(item => item.channel_type?.includes('GENERAL'));
    const exportData = combinedPriceData.historical.filter(item => item.channel_type?.includes('FEEDIN'));

    const currentImport = importData.length > 0 && importData[importData.length - 1]?.per_kwh !== undefined 
      ? Number(importData[importData.length - 1].per_kwh) || 0 : 0;
    const currentExport = exportData.length > 0 && exportData[exportData.length - 1]?.per_kwh !== undefined 
      ? Number(exportData[exportData.length - 1].per_kwh) || 0 : 0;

    return {
      currentImport: Number(currentImport) || 0,
      currentExport: Number(currentExport) || 0
    };
  };

  const priceSummary = calculatePriceSummary();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-8">Amber Electric</h1>
        
        {priceSummary && (
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600">Import</div>
              <div className="text-3xl font-bold text-gray-900">
                {priceSummary.currentImport.toFixed(1)}¢
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <div className="text-sm text-gray-600">Export</div>
              <div className="text-3xl font-bold text-gray-900">
                {priceSummary.currentExport.toFixed(1)}¢
              </div>
            </div>
          </div>
        )}

        <div className="bg-white p-6 rounded-lg border">
          <CombinedPriceChart data={combinedPriceData} />
        </div>
      </div>
    </div>
  );
}
