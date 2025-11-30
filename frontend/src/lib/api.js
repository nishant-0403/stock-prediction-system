import axios from 'axios';

export const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
//export const API_BASE = `${API_URL}/api`;
export const API_BASE = `${API_URL}`;

// axios instance configured with baseURL and automatic Authorization header
export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// attach token from localStorage if present
apiClient.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('stock_user');
    if (stored) {
      const user = JSON.parse(stored);
      if (user.token || user.access_token) {
        const token = user.token || user.access_token;
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  } catch (e) {
    // ignore parse errors
  }
  return config;
});

// Authentication
export async function login(payload) {
  const res = await apiClient.post('/login', payload);
  return res.data;
}

export async function register(payload) {
  const res = await apiClient.post('/register', payload);
  return res.data;
}

//Watchlist
export async function getWatchlist(user_id) {
  const res = await apiClient.post('/watchlist', { user_id });
  return res.data;
}

export async function addToWatchlist(payload) {
  const res = await apiClient.post('/watchlist/add', payload);
  return res.data;
}

export async function removeFromWatchlist(payload) {
  const res = await apiClient.post('/watchlist/remove', payload);
  return res.data;
}

// Thresholds
export async function getThresholds(user_id) {
  const res = await apiClient.post('/threshold', { user_id });
  return res.data;
}

export async function setThreshold(payload) {
  const res = await apiClient.post('/threshold/set', payload);
  return res.data;
}

// Stocks
export async function getAvailableStocks() {
  const res = await apiClient.get('/stocks/available');
  return res.data;
}

export async function getStockHistory(symbol) {
  const res = await apiClient.get(`/stocks/${encodeURIComponent(symbol)}/history`);
  return res.data;
}

// Check threshold for a stock_id
export async function checkThreshold(stock_id, user_id) {
  const res = await apiClient.get(`/stocks/${stock_id}/check-threshold/${user_id}`);
  return res.data;
}

// Predict: backend exposes GET /api/predict?stock_id=...
export async function predictStockById(stock_id) {
  const res = await apiClient.get(`/predict?stock_id=${encodeURIComponent(stock_id)}`);
  return res.data;
}
