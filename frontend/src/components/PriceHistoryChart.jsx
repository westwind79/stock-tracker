import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import axios from 'axios';
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

const DATA_PATH = process.env.PUBLIC_URL + '/data';

const PriceHistoryChart = () => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);
  const [priceData, setPriceData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPriceHistory = async () => {
      try {
        const response = await axios.get(`${DATA_PATH}/price_history.json`);
        setPriceData(response.data || []);
      } catch (error) {
        console.error('Error fetching price history:', error);
        setPriceData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPriceHistory();
  }, []);

  useEffect(() => {
    if (!chartRef.current || priceData.length === 0) return;

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    // Prepare data for Chart.js
    const labels = priceData.map(d => d.date).reverse();
    const prices = priceData.map(d => d.price).reverse();

    // Create gradient
    const ctx = chartRef.current.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

    // Create chart
    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Insider Transaction Price (USD)',
          data: prices,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: gradient,
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgb(59, 130, 246)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 12,
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: 'rgb(59, 130, 246)',
            borderWidth: 1,
            displayColors: false,
            callbacks: {
              title: (context) => {
                return `Date: ${context[0].label}`;
              },
              label: (context) => {
                return `Price: $${context.parsed.y.toFixed(2)}`;
              },
              afterLabel: (context) => {
                const dataPoint = priceData[priceData.length - 1 - context.dataIndex];
                return `Transactions: ${dataPoint.transactions}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              autoSkip: true,
              maxTicksLimit: 10,
            }
          },
          y: {
            beginAtZero: false,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)',
            },
            ticks: {
              callback: function(value) {
                return '$' + value.toFixed(0);
              }
            }
          }
        }
      }
    });

    // Cleanup
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [priceData]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Insider Transaction Price History</CardTitle>
          <CardDescription>Loading price data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (priceData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Insider Transaction Price History</CardTitle>
          <CardDescription>No price data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[400px] flex items-center justify-center text-slate-500">
            <p>No historical price data found. Run the data generator to create price_history.json</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate stats
  const prices = priceData.map(d => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const currentPrice = priceData[0]?.price || 0;
  const oldestPrice = priceData[priceData.length - 1]?.price || 0;
  const priceChange = currentPrice - oldestPrice;
  const priceChangePercent = oldestPrice > 0 ? (priceChange / oldestPrice) * 100 : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Insider Transaction Price History</CardTitle>
            <CardDescription>
              Average insider transaction prices • {priceData.length} data points
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">${currentPrice.toFixed(2)}</div>
            <div className={`text-sm ${priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {priceChange >= 0 ? '+' : ''}{priceChangePercent.toFixed(2)}%
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[400px] relative">
          <canvas ref={chartRef}></canvas>
        </div>
        
        {/* Price Stats */}
        <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t">
          <div>
            <p className="text-xs text-slate-600">Current</p>
            <p className="text-lg font-semibold">${currentPrice.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-600">High</p>
            <p className="text-lg font-semibold text-green-600">${maxPrice.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-xs text-slate-600">Low</p>
            <p className="text-lg font-semibold text-red-600">${minPrice.toFixed(2)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PriceHistoryChart;