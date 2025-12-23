import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DollarSign, TrendingUp, Building2 } from "lucide-react";

ChartJS.register(CategoryScale, LinearScale, PointElement, Tooltip, Legend);

const InstitutionalOwnershipMap = () => {
  const [clusterData, setClusterData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const DATA_PATH = process.env.PUBLIC_URL + '/data';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [clusterRes, statsRes] = await Promise.all([
          axios.get(`${DATA_PATH}/ownership_cluster.json`),
          axios.get(`${DATA_PATH}/institutional_ownership.json`)
        ]);
        
        setClusterData(Array.isArray(clusterRes.data) ? clusterRes.data : []);
        setStats(statsRes.data);
      } catch (error) {
        console.error('Error loading institutional ownership data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [DATA_PATH]);

  const formatCurrency = (value) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  };

  const formatShares = (value) => {
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
    return value.toLocaleString();
  };

  // Generate bubble chart data
  const bubbleData = {
    datasets: clusterData.map((investor, index) => {
      // Color palette for different investors
      const colors = [
        'rgba(59, 130, 246, 0.7)',   // Blue - Vanguard
        'rgba(16, 185, 129, 0.7)',   // Green - BlackRock
        'rgba(245, 158, 11, 0.7)',   // Orange - State Street
        'rgba(139, 92, 246, 0.7)',   // Purple - Fidelity
        'rgba(236, 72, 153, 0.7)',   // Pink - Others
        'rgba(99, 102, 241, 0.7)',   // Indigo
        'rgba(239, 68, 68, 0.7)',    // Red
      ];
      
      const borderColors = [
        'rgb(59, 130, 246)',
        'rgb(16, 185, 129)',
        'rgb(245, 158, 11)',
        'rgb(139, 92, 246)',
        'rgb(236, 72, 153)',
        'rgb(99, 102, 241)',
        'rgb(239, 68, 68)',
      ];

      return {
        label: investor.name,
        data: [{
          x: index * 100, // Spread horizontally
          y: investor.shares / 1000000, // Millions of shares (y-axis)
          r: Math.sqrt(investor.value) / 3000, // Bubble size based on value
        }],
        backgroundColor: colors[index % colors.length],
        borderColor: borderColors[index % colors.length],
        borderWidth: 2,
      };
    }),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          boxWidth: 15,
          padding: 15,
          font: {
            size: 11,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const investor = clusterData[context.datasetIndex];
            return [
              `${investor.name}`,
              `Shares: ${formatShares(investor.shares)}`,
              `Value: ${formatCurrency(investor.value)}`,
              `Filed: ${investor.filing_date}`,
            ];
          },
        },
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
          weight: 'bold',
        },
        bodyFont: {
          size: 12,
        },
      },
    },
    scales: {
      x: {
        display: false, // Hide x-axis (just for spacing)
      },
      y: {
        title: {
          display: true,
          text: 'Shares Held (Millions)',
          font: {
            size: 12,
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
        ticks: {
          callback: function(value) {
            return value.toFixed(1) + 'M';
          },
        },
      },
    },
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Institutional Ownership Map</CardTitle>
          <CardDescription>Loading institutional investor data...</CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[400px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!clusterData || clusterData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Institutional Ownership Map</CardTitle>
          <CardDescription>No institutional ownership data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 text-slate-500">
            <Building2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Run the institutional ownership scraper to generate data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Institutional Value</CardTitle>
              <DollarSign className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {formatCurrency(stats.total_institutional_value)}
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {formatShares(stats.total_institutional_shares)} shares
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Number of Institutions</CardTitle>
              <Building2 className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {stats.number_of_institutions}
              </div>
              <p className="text-xs text-slate-600 mt-1">Major institutional holders</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Largest Holder</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-lg font-bold text-purple-600 truncate">
                {stats.largest_holder}
              </div>
              <p className="text-xs text-slate-600 mt-1">
                {formatShares(stats.largest_holder_shares)} shares
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Bubble Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Institutional Ownership Cluster Map</CardTitle>
          <CardDescription>
            Bubble size represents total position value • SEC Form 13F filings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px]">
            <Scatter data={bubbleData} options={options} />
          </div>
        </CardContent>
      </Card>

      {/* Top Holders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Top Institutional Holders</CardTitle>
          <CardDescription>Ranked by number of shares held</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {clusterData.slice(0, 10).map((investor, idx) => (
              <div 
                key={idx}
                className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold text-slate-300 w-8">
                    {idx + 1}
                  </div>
                  <div>
                    <h3 className="font-semibold">{investor.name}</h3>
                    <p className="text-sm text-slate-600">
                      Filed: {investor.filing_date}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-lg">
                    {formatShares(investor.shares)}
                  </div>
                  <p className="text-sm text-slate-600">
                    {formatCurrency(investor.value)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default InstitutionalOwnershipMap;