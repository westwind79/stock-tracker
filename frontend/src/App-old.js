import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, TrendingDown, Users, DollarSign, Calendar } from "lucide-react";
import { toast } from "sonner";

// Use static JSON files from /data folder
const DATA_PATH = process.env.PUBLIC_URL + '/data';

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [stats, setStats] = useState(null);
  const [executives, setExecutives] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState('all');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [transRes, statsRes, execRes] = await Promise.all([
        axios.get(`${DATA_PATH}/transactions.json`),
        axios.get(`${DATA_PATH}/stats.json`),
        axios.get(`${DATA_PATH}/executives.json`)
      ]);
      
      // Ensure data is in correct format
      setTransactions(Array.isArray(transRes.data) ? transRes.data : []);
      setStats(statsRes.data);
      setExecutives(Array.isArray(execRes.data) ? execRes.data : []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data. Make sure JSON files are uploaded to /data folder.');
      // Set empty defaults
      setTransactions([]);
      setExecutives([]);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    // For static JSON, "refresh" just reloads the files
    setRefreshing(true);
    toast.info('Reloading data from server...');
    
    try {
      await fetchData();
      toast.success('Data reloaded successfully!');
    } catch (error) {
      toast.error('Failed to reload data');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

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

  const filteredTransactions = transactions.filter(t => {
    if (filter === 'all') return true;
    if (filter === 'sales') return t.transaction_type === 'Sale';
    if (filter === 'purchases') return t.transaction_type === 'Purchase';
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-lg">Loading insider trading data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900" data-testid="main-heading">
                Workday Insider Trading Tracker
              </h1>
              <p className="text-sm text-slate-600 mt-1">Live SEC EDGAR data • WDAY</p>
            </div>
            <Button
              onClick={refreshData}
              disabled={refreshing}
              className="gap-2"
              data-testid="refresh-button"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card data-testid="total-sales-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sales Volume</CardTitle>
              <DollarSign className="h-4 w-4 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats ? formatCurrency(stats.total_sales_value) : '$0'}
              </div>
              <p className="text-xs text-slate-600 mt-1">From Form 4 filings</p>
            </CardContent>
          </Card>

          <Card data-testid="total-transactions-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Transactions</CardTitle>
              <TrendingDown className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats ? stats.total_transactions : 0}
              </div>
              <p className="text-xs text-slate-600 mt-1">Buy & Sell orders</p>
            </CardContent>
          </Card>

          <Card data-testid="unique-executives-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Executives</CardTitle>
              <Users className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats ? stats.unique_executives : 0}
              </div>
              <p className="text-xs text-slate-600 mt-1">Reporting insiders</p>
            </CardContent>
          </Card>

          <Card data-testid="last-updated-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Last Updated</CardTitle>
              <Calendar className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-sm font-semibold">
                {stats ? stats.last_updated : 'Never'}
              </div>
              <p className="text-xs text-slate-600 mt-1">Data refresh time</p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="transactions" className="space-y-4">
          <TabsList data-testid="main-tabs">
            <TabsTrigger value="transactions" data-testid="transactions-tab">All Transactions</TabsTrigger>
            <TabsTrigger value="executives" data-testid="executives-tab">By Executive</TabsTrigger>
          </TabsList>

          {/* Transactions Tab */}
          <TabsContent value="transactions" className="space-y-4">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Transaction History</CardTitle>
                    <CardDescription>Recent insider trading activity from SEC Form 4 filings</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant={filter === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('all')}
                      data-testid="filter-all"
                    >
                      All
                    </Button>
                    <Button
                      variant={filter === 'sales' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('sales')}
                      data-testid="filter-sales"
                    >
                      Sales Only
                    </Button>
                    <Button
                      variant={filter === 'purchases' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilter('purchases')}
                      data-testid="filter-purchases"
                    >
                      Purchases Only
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {filteredTransactions.length === 0 ? (
                  <div className="text-center py-12" data-testid="no-transactions">
                    <p className="text-slate-500">No transactions found. Make sure JSON files are uploaded.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table data-testid="transactions-table">
                      <TableHeader>
                        <TableRow>
                          <TableHead>Executive</TableHead>
                          <TableHead>Title</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead className="text-right">Shares</TableHead>
                          <TableHead className="text-right">Price</TableHead>
                          <TableHead className="text-right">Total Value</TableHead>
                          <TableHead>Transaction Date</TableHead>
                          <TableHead>Filing Date</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredTransactions.map((trans) => (
                          <TableRow key={trans.id} data-testid={`transaction-row-${trans.id}`}>
                            <TableCell className="font-medium">{trans.executive_name}</TableCell>
                            <TableCell className="text-sm text-slate-600">{trans.executive_title}</TableCell>
                            <TableCell>
                              <Badge
                                variant={trans.transaction_type === 'Sale' ? 'destructive' : 'default'}
                                data-testid={`transaction-type-${trans.id}`}
                              >
                                {trans.transaction_type}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">{formatNumber(trans.shares)}</TableCell>
                            <TableCell className="text-right">${trans.price_per_share.toFixed(2)}</TableCell>
                            <TableCell className="text-right font-semibold">
                              {formatCurrency(trans.total_value)}
                            </TableCell>
                            <TableCell>{trans.transaction_date}</TableCell>
                            <TableCell className="text-sm text-slate-600">{trans.filing_date}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Executives Tab */}
          <TabsContent value="executives" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Executive Summary</CardTitle>
                <CardDescription>Aggregated trading activity by executive</CardDescription>
              </CardHeader>
              <CardContent>
                {executives.length === 0 ? (
                  <div className="text-center py-12" data-testid="no-executives">
                    <p className="text-slate-500">No executive data available.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {executives.map((exec, idx) => (
                      <div
                        key={exec.name}
                        className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 transition-colors"
                        data-testid={`executive-card-${idx}`}
                      >
                        <div className="flex-1">
                          <h3 className="font-semibold text-lg">{exec.name}</h3>
                          <p className="text-sm text-slate-600 mt-1">
                            {exec.transaction_count} transactions • Last: {exec.latest_transaction}
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-bold text-red-600">
                            {formatCurrency(exec.total_sales)}
                          </div>
                          <p className="text-xs text-slate-600">Total sales</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-slate-500">
          <p>Data sourced from SEC EDGAR • Updated periodically</p>
          <p className="mt-1">Workday Inc. (WDAY) • CIK: 0001327811</p>
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter basename="/workday">
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;