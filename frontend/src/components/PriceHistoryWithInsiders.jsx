// Enhanced Price History Chart with Insider Transaction Markers
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const PriceHistoryWithInsiders = () => {
  const [priceData, setPriceData] = useState(null);
  const [insiderData, setInsiderData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [priceRes, insiderRes] = await Promise.all([
          fetch(`${process.env.PUBLIC_URL}/data/price_history.json`),
          fetch(`${process.env.PUBLIC_URL}/data/transactions.json`)
        ]);
        
        const prices = await priceRes.json();
        const insiders = await insiderRes.json();
        
        setPriceData(prices);
        setInsiderData(insiders);
      } catch (error) {
        console.error('Error loading data:', error);
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
          <CardTitle>Stock Price & Insider Transactions</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!priceData || !priceData.dates || priceData.dates.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Stock Price & Insider Transactions</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Process insider transactions
  const insiderSales = [];
  const insiderPurchases = [];
  
  if (insiderData && Array.isArray(insiderData)) {
    insiderData.forEach(transaction => {
      const transactionPoint = {
        x: transaction.transaction_date,
        y: transaction.price_per_share,
        executive: transaction.executive_name,
        shares: transaction.shares,
        value: transaction.total_value,
        type: transaction.transaction_type
      };
      
      if (transaction.transaction_type === 'Sale') {
        insiderSales.push(transactionPoint);
      } else if (transaction.transaction_type === 'Purchase') {
        insiderPurchases.push(transactionPoint);
      }
    });
  }

  const chartData = {
    labels: priceData.dates,
    datasets: [
      {
        label: 'Stock Price',
        data: priceData.prices,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 5,
        borderWidth: 2,
      },
      {
        label: 'Insider Sales',
        data: insiderSales,
        type: 'scatter',
        backgroundColor: 'rgb(239, 68, 68)',
        borderColor: 'rgb(220, 38, 38)',
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'triangle',
        rotation: 180, // Point down
      },
      {
        label: 'Insider Purchases',
        data: insiderPurchases,
        type: 'scatter',
        backgroundColor: 'rgb(34, 197, 94)',
        borderColor: 'rgb(22, 163, 74)',
        pointRadius: 8,
        pointHoverRadius: 10,
        pointStyle: 'triangle',
        rotation: 0, // Point up
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'nearest',
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        enabled: true,
        callbacks: {
          label: function(context) {
            if (context.dataset.label === 'Stock Price') {
              return `Price: $${context.parsed.y.toFixed(2)}`;
            } else {
              // Insider transaction
              const point = context.raw;
              const formatted = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(point.value);
              
              return [
                `${point.executive}`,
                `${point.type}: ${point.shares.toLocaleString()} shares`,
                `Price: $${point.y.toFixed(2)}`,
                `Total: ${formatted}`
              ];
            }
          }
        }
      },
      title: {
        display: true,
        text: 'WDAY Stock Price with Insider Transaction Points',
        font: {
          size: 16,
        },
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date',
        },
        ticks: {
          maxRotation: 45,
          minRotation: 45,
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Price (USD)',
        },
        ticks: {
          callback: function(value) {
            return '$' + value.toFixed(0);
          }
        }
      },
    },
  };

  // Calculate stats
  const currentPrice = priceData.prices[priceData.prices.length - 1];
  const startPrice = priceData.prices[0];
  const priceChange = currentPrice - startPrice;
  const priceChangePercent = ((priceChange / startPrice) * 100).toFixed(2);
  
  const totalSales = insiderSales.reduce((sum, s) => sum + s.value, 0);
  const totalPurchases = insiderPurchases.reduce((sum, p) => sum + p.value, 0);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Current Price</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              ${currentPrice?.toFixed(2) || 'N/A'}
            </div>
            <p className={`text-sm font-medium mt-1 ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {priceChange >= 0 ? '↑' : '↓'} {Math.abs(priceChangePercent)}% (90d)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Insider Sales</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {insiderSales.length}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              ${(totalSales / 1000000).toFixed(1)}M total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Insider Purchases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {insiderPurchases.length}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              ${(totalPurchases / 1000000).toFixed(1)}M total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-slate-600">Data Range</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-purple-600">
              90 Days
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {priceData.dates.length} trading days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Stock Price History with Insider Transactions</CardTitle>
          <CardDescription>
            🔺 Green triangles = Insider Purchases • 🔻 Red triangles = Insider Sales
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[500px]">
            <Line data={chartData} options={options} />
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How to Read This Chart</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2 text-blue-600">📈 Blue Line</h4>
              <p className="text-slate-600">Daily closing stock price over the last 90 days</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 text-red-600">🔻 Red Triangles (pointing down)</h4>
              <p className="text-slate-600">Insider sales - executives selling WDAY stock at that price point</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 text-green-600">🔺 Green Triangles (pointing up)</h4>
              <p className="text-slate-600">Insider purchases - executives buying WDAY stock at that price point</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 text-purple-600">💡 Hover for Details</h4>
              <p className="text-slate-600">Hover over any triangle to see executive name, share count, and transaction value</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PriceHistoryWithInsiders;