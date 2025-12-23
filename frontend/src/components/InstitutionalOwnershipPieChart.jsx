// Institutional Ownership - PIE CHART Version
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  Title
} from 'chart.js';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, Title);

const InstitutionalOwnershipPieChart = () => {
  const [ownershipData, setOwnershipData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch(`${process.env.PUBLIC_URL}/data/institutional_ownership.json`);
        const data = await response.json();
        setOwnershipData(data);
      } catch (error) {
        console.error('Error loading institutional ownership data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Institutional Ownership</CardTitle>
          <CardDescription>Loading data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!ownershipData || !ownershipData.holdings_by_investor || ownershipData.holdings_by_investor.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Institutional Ownership</CardTitle>
          <CardDescription>No institutional ownership data available</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 text-center py-12">
            Run the institutional ownership scraper to generate data.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Prepare data for pie chart
  const topHolders = ownershipData.holdings_by_investor.slice(0, 8); // Top 8
  const othersValue = ownershipData.holdings_by_investor
    .slice(8)
    .reduce((sum, holder) => sum + holder.value_dollars, 0);

  const pieLabels = [...topHolders.map(h => h.investor_name)];
  const pieValues = [...topHolders.map(h => h.value_dollars)];

  if (othersValue > 0) {
    pieLabels.push('Others');
    pieValues.push(othersValue);
  }

  // Color palette
  const colors = [
    '#3b82f6', // blue
    '#10b981', // green
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // purple
    '#ec4899', // pink
    '#06b6d4', // cyan
    '#f97316', // orange
    '#94a3b8', // slate (for "Others")
  ];

  const pieData = {
    labels: pieLabels,
    datasets: [
      {
        data: pieValues,
        backgroundColor: colors,
        borderColor: '#ffffff',
        borderWidth: 2,
      }
    ]
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
          generateLabels: (chart) => {
            const data = chart.data;
            return data.labels.map((label, i) => {
              const value = data.datasets[0].data[i];
              const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              
              return {
                text: `${label} (${percentage}%)`,
                fillStyle: data.datasets[0].backgroundColor[i],
                hidden: false,
                index: i,
              };
            });
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            const formatted = new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(value);
            return `${context.label}: ${formatted} (${percentage}%)`;
          }
        }
      },
      title: {
        display: true,
        text: 'Distribution of Institutional Holdings',
        font: {
          size: 16,
        },
      },
    },
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  return (
    <div className="space-y-6 mb-8">
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Total Institutional Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(ownershipData.total_institutional_value)}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {formatNumber(ownershipData.total_institutional_shares)} shares
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Number of Institutions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {ownershipData.number_of_institutions}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Major institutional holders
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Largest Holder</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-purple-600">
              {ownershipData.largest_holder}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {formatNumber(ownershipData.largest_holder_shares)} shares
            </p>
          </CardContent>
        </Card>
      </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Institutional Ownership Distribution</CardTitle>
            <CardDescription>
              Based on most recent 13F filings • Last updated: {ownershipData.last_updated}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[500px]">
              <Pie data={pieData} options={pieOptions} />
            </div>
          </CardContent>
        </Card>

        {/* Top Holders Table */}
        <Card>
          <CardHeader>
            <CardTitle>Top Institutional Holders</CardTitle>
            <CardDescription>Sorted by total value of holdings</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-2 font-semibold text-sm">Rank</th>
                    <th className="text-left py-3 px-2 font-semibold text-sm">Institution</th>
                    <th className="text-right py-3 px-2 font-semibold text-sm">Shares</th>
                    <th className="text-right py-3 px-2 font-semibold text-sm">Value</th>
                    <th className="text-right py-3 px-2 font-semibold text-sm">% of Total</th>
                    <th className="text-right py-3 px-2 font-semibold text-sm">Filing Date</th>
                  </tr>
                </thead>
                <tbody>
                  {ownershipData.holdings_by_investor.slice(0, 15).map((holder, idx) => {
                    const percentage = (holder.value_dollars / ownershipData.total_institutional_value * 100).toFixed(2);
                    return (
                      <tr key={idx} className="border-b hover:bg-slate-50">
                        <td className="py-3 px-2 text-sm">{idx + 1}</td>
                        <td className="py-3 px-2 font-medium text-sm">{holder.investor_name}</td>
                        <td className="py-3 px-2 text-right text-sm">{formatNumber(holder.shares)}</td>
                        <td className="py-3 px-2 text-right text-sm font-semibold">
                          {formatCurrency(holder.value_dollars)}
                        </td>
                        <td className="py-3 px-2 text-right text-sm">{percentage}%</td>
                        <td className="py-3 px-2 text-right text-sm text-slate-600">
                          {holder.filing_date}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InstitutionalOwnershipPieChart;