import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'sonner';
import { getStockHistory } from '@/lib/api';

/*
export default function StockChart({ symbol }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        //const data = await getStockHistory(symbol);
        const formattedData = data.history.map(item => ({
          time: new Date(item.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          price: item.price
        }));
        setChartData(formattedData);
      } catch (error) {
        toast.error('Failed to load chart data');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 60000); // Refresh every minute

    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) {
    return <div className="h-64 flex items-center justify-center text-gray-500">Loading chart...</div>;
  }

  return (
    <div className="h-80" data-testid="stock-chart">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="time" 
            tick={{ fontSize: 12 }}
            stroke="#666"
          />
          <YAxis 
            domain={['auto', 'auto']} 
            tick={{ fontSize: 12 }}
            stroke="#666"
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(255, 255, 255, 0.95)',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#14b8a6" 
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, fill: '#14b8a6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
*/

export default function StockChart({ symbol, prediction }) {
  if (!symbol) {
    return (
      <div style={{ textAlign: "center", color: "gray" }}>
        Select a stock to see prediction
      </div>
    );
  }

  if (!prediction) {
    return (
      <div style={{ textAlign: "center", color: "gray" }}>
        Loading prediction...
      </div>
    );
  }

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h2 className="text-xl font-semibold">Prediction for {symbol}</h2>

      <p className="text-2xl mt-4">
        Predicted Price:{" "}
        <span className="font-bold text-blue-600">
          ${prediction.predicted_price.toFixed(2)}
        </span>
      </p>

      {prediction.confidence !== undefined && (
        <p className="text-gray-500 mt-2">
          Confidence: {(prediction.confidence * 100).toFixed(0)}%
        </p>
      )}
    </div>
  );
}

