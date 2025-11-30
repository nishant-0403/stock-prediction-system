import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { TrendingUp, TrendingDown, LogOut, Plus, Trash2, Bell } from 'lucide-react';
import StockChart from '@/components/StockChart';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getWatchlist, getThresholds, getAvailableStocks, addToWatchlist, removeFromWatchlist, setThreshold as setThresholdApi, checkThreshold } from '@/lib/api';


const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";
const API = `${BACKEND_URL}`;


export default function Dashboard({ user, onLogout }) {
  const [watchlist, setWatchlist] = useState([]);
  const [thresholds, setThresholds] = useState([]);
  const [availableStocks, setAvailableStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [loading, setLoading] = useState(true);
  const [addStockDialog, setAddStockDialog] = useState(false);
  const [thresholdDialog, setThresholdDialog] = useState(false);
  const [selectedForThreshold, setSelectedForThreshold] = useState(null);
  const [thresholdForm, setThresholdForm] = useState({
    threshold_no: 1,
    upper_limit: '',
    lower_limit: ''
  });

  const fetchWatchlist = useCallback(async () => {
    try {
      const data = await getWatchlist(user.user_id);
      setWatchlist(data);
      if (data.length > 0 && !selectedStock) {
        setSelectedStock(data[0]);
      }
    } catch (error) {
      toast.error('Failed to fetch watchlist');
    }
  }, [user.user_id, selectedStock]);

  const fetchThresholds = useCallback(async () => {
    try {
      const data = await getThresholds(user.user_id);
      setThresholds(data);
    } catch (error) {
      console.error('Failed to fetch thresholds', error);
    }
  }, [user.user_id]);

  const fetchAvailableStocks = async () => {
    try {
      const data = await getAvailableStocks();
      setAvailableStocks(data);
    } catch (error) {
      toast.error('Failed to fetch available stocks');
    }
  };

  const checkThresholdBreaches = useCallback(async () => {
    for (const item of watchlist) {
      try {
        const data = await checkThreshold(item.stock_id, user.user_id);
        if (data.breaches.length > 0) {
          data.breaches.forEach(breach => {
            toast.warning(
              `${breach.symbol}: Price ${breach.current_price} breached ${breach.type} limit of ${breach.limit}`,
              { duration: 5000 }
            );
          });
        }
      } catch (error) {
        console.error('Failed to check thresholds', error);
      }
    }
  }, [watchlist, user.user_id]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await fetchWatchlist();
      await fetchThresholds();
      await fetchAvailableStocks();
      setLoading(false);
    };
    init();
  }, [fetchWatchlist, fetchThresholds]);

  useEffect(() => {
    const interval = setInterval(() => {
      fetchWatchlist();
      checkThresholdBreaches();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [fetchWatchlist, checkThresholdBreaches]);

  /*
  const handleAddStock = async (symbol) => {
    try {
      await addToWatchlist({
        symbol,
        user_id: user.user_id
      });
      toast.success(`${symbol} added to watchlist`);
      await fetchWatchlist();
      setAddStockDialog(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add stock');
    }
  };
  */
    const handleAddStock = async () => {
	const symbol = window.prompt("Enter the stock symbol to add to your watchlist:");

	if (!symbol) {
	    toast.error("Symbol cannot be empty");
	    return;
	}

	try {
	    await addToWatchlist({
		symbol: symbol.trim().toUpperCase(),
		user_id: user.user_id || user.id,
	    });
	    toast.success(`Added ${symbol.toUpperCase()} to your watchlist`);
	    await loadWatchlist(); // refresh list if your code has such function
	} catch (err) {
	    console.error(err);
	    toast.error("Failed to add to watchlist");
	}
    };

  const handleRemoveStock = async (stockId) => {
    try {
      await removeFromWatchlist({
        user_id: user.user_id,
        stock_id: stockId
      });
      toast.success('Stock removed from watchlist');
      await fetchWatchlist();
      if (selectedStock?.stock_id === stockId) {
        setSelectedStock(watchlist.find(s => s.stock_id !== stockId) || null);
      }
    } catch (error) {
      toast.error('Failed to remove stock');
    }
  };

  const handleSetThreshold = async () => {
    if (!thresholdForm.upper_limit || !thresholdForm.lower_limit) {
      toast.error('Please fill in both limits');
      return;
    }

    try {
      await setThresholdApi({
        user_id: user.user_id,
        stock_id: selectedForThreshold.stock_id,
        threshold_no: thresholdForm.threshold_no,
        upper_limit: parseFloat(thresholdForm.upper_limit),
        lower_limit: parseFloat(thresholdForm.lower_limit)
      });
      toast.success('Threshold set successfully');
      await fetchThresholds();
      setThresholdDialog(false);
      setThresholdForm({ threshold_no: 1, upper_limit: '', lower_limit: '' });
    } catch (error) {
      toast.error('Failed to set threshold');
    }
  };

  const getSignalColor = (changePercent) => {
    if (changePercent > 2) return 'text-green-600';
    if (changePercent < -2) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSignalBadge = (changePercent) => {
    if (changePercent > 2) return <Badge className="bg-green-500">BUY</Badge>;
    if (changePercent < -2) return <Badge className="bg-red-500">SELL</Badge>;
    return <Badge className="bg-yellow-500 text-black">HOLD</Badge>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" data-testid="loading-screen">
        <div className="text-xl font-medium">Loading your dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e0f7fa 0%, #f1f8e9 100%)' }}>
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-teal-500 to-cyan-600 p-2 rounded-xl" data-testid="dashboard-logo">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }} data-testid="dashboard-title">
                  Stock Monitor
                </h1>
                <p className="text-sm text-gray-600">Welcome, {user.name}</p>
              </div>
            </div>
            <Button 
              onClick={onLogout} 
              variant="outline" 
              className="flex items-center space-x-2"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chart Area */}
          <div className="lg:col-span-2 space-y-6">
            {selectedStock ? (
              <>
                <Card className="shadow-lg border-0" data-testid="selected-stock-card">
                  <CardHeader className="pb-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-3xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }} data-testid="stock-symbol">
                          {selectedStock.symbol}
                        </CardTitle>
                        <CardDescription className="text-base mt-1" data-testid="stock-name">{selectedStock.name}</CardDescription>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold" data-testid="stock-price">${selectedStock.current_price}</div>
                        <div className={`flex items-center justify-end space-x-1 ${getSignalColor(selectedStock.change_percent)}`}>
                          {selectedStock.change_percent > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                          <span className="font-medium" data-testid="stock-change">{selectedStock.change_percent > 0 ? '+' : ''}{selectedStock.change_percent}%</span>
                        </div>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="mb-4">
                      {getSignalBadge(selectedStock.change_percent)}
                    </div>
                    <StockChart symbol={selectedStock.symbol} />
                  </CardContent>
                </Card>

                {/* Threshold Management */}
                <Card className="shadow-lg border-0" data-testid="threshold-card">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xl font-bold" data-testid="threshold-title">Price Alerts</CardTitle>
                      <Dialog open={thresholdDialog} onOpenChange={setThresholdDialog}>
                        <DialogTrigger asChild>
                          <Button 
                            size="sm"
                            className="bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700"
                            onClick={() => setSelectedForThreshold(selectedStock)}
                            data-testid="set-alert-button"
                          >
                            <Bell className="w-4 h-4 mr-2" />
                            Set Alert
                          </Button>
                        </DialogTrigger>
                        <DialogContent data-testid="threshold-dialog">
                          <DialogHeader>
                            <DialogTitle>Set Price Alert for {selectedForThreshold?.symbol}</DialogTitle>
                            <DialogDescription>
                              Get notified when the price crosses these limits
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4 mt-4">
                            <div className="space-y-2">
                              <label className="text-sm font-medium">Threshold Number</label>
                              <Select 
                                value={thresholdForm.threshold_no.toString()}
                                onValueChange={(val) => setThresholdForm({...thresholdForm, threshold_no: parseInt(val)})}
                              >
                                <SelectTrigger data-testid="threshold-number-select">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="1">Threshold 1</SelectItem>
                                  <SelectItem value="2">Threshold 2</SelectItem>
                                  <SelectItem value="3">Threshold 3</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-medium">Upper Limit ($)</label>
                              <Input
                                type="number"
                                step="0.01"
                                placeholder="200.00"
                                value={thresholdForm.upper_limit}
                                onChange={(e) => setThresholdForm({...thresholdForm, upper_limit: e.target.value})}
                                data-testid="upper-limit-input"
                              />
                            </div>
                            <div className="space-y-2">
                              <label className="text-sm font-medium">Lower Limit ($)</label>
                              <Input
                                type="number"
                                step="0.01"
                                placeholder="150.00"
                                value={thresholdForm.lower_limit}
                                onChange={(e) => setThresholdForm({...thresholdForm, lower_limit: e.target.value})}
                                data-testid="lower-limit-input"
                              />
                            </div>
                            <Button 
                              onClick={handleSetThreshold} 
                              className="w-full bg-gradient-to-r from-teal-500 to-cyan-600"
                              data-testid="save-threshold-button"
                            >
                              Save Alert
                            </Button>
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {thresholds.filter(t => t.stock_id === selectedStock.stock_id).length > 0 ? (
                      <div className="space-y-2" data-testid="threshold-list">
                        {thresholds.filter(t => t.stock_id === selectedStock.stock_id).map((threshold, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg" data-testid={`threshold-item-${idx}`}>
                            <div>
                              <div className="font-medium">Threshold {threshold.threshold_no}</div>
                              <div className="text-sm text-gray-600">
                                ${threshold.lower_limit} - ${threshold.upper_limit}
                              </div>
                            </div>
                            <Badge variant="outline">Active</Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-center py-4" data-testid="no-thresholds">No alerts set for this stock</p>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="shadow-lg border-0" data-testid="no-stocks-card">
                <CardContent className="py-12 text-center">
                  <TrendingUp className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-xl font-semibold mb-2">No Stocks in Watchlist</h3>
                  <p className="text-gray-600 mb-4">Add stocks to start monitoring</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Watchlist Sidebar */}
          <div className="space-y-6">
            <Card className="shadow-lg border-0" data-testid="watchlist-card">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-bold">Watchlist</CardTitle>
                </div>
      <Button
      size="sm"
      className="bg-gradient-to-r from-teal-500 to-cyan-600"
      data-testid="add-stock-button"
      onClick={handleAddStock}
      >
      <Plus className="w-4 h-4 mr-2" />
      Add
      </Button>
              </CardHeader>
              <CardContent className="space-y-2">
                {watchlist.length > 0 ? (
                  watchlist.map((stock) => (
                    <div
                      key={stock.stock_id}
                      className={`p-3 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                        selectedStock?.stock_id === stock.stock_id
                          ? 'bg-gradient-to-r from-teal-50 to-cyan-50 border-2 border-teal-500'
                          : 'bg-gray-50 hover:bg-gray-100'
                      }`}
                      onClick={() => setSelectedStock(stock)}
                      data-testid={`watchlist-item-${stock.symbol}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-bold">{stock.symbol}</div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveStock(stock.stock_id);
                          }}
                          className="text-red-500 hover:text-red-700 p-1 hover:bg-red-50 rounded transition-colors"
                          data-testid={`remove-stock-${stock.symbol}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="text-sm text-gray-600 mb-1">{stock.name}</div>
                      <div className="flex items-center justify-between">
                        <div className="font-medium">${stock.current_price}</div>
                        <div className={`flex items-center space-x-1 text-sm ${getSignalColor(stock.change_percent)}`}>
                          {stock.change_percent > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          <span>{stock.change_percent > 0 ? '+' : ''}{stock.change_percent}%</span>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4" data-testid="empty-watchlist">Your watchlist is empty</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
