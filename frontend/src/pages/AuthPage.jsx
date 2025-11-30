import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { TrendingUp } from 'lucide-react';
import { login, register } from '@/lib/api';

export default function AuthPage({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    telegram_id: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : { 
            name: formData.name, 
            email: formData.email, 
            password: formData.password,
            telegram_id: formData.telegram_id ? parseInt(formData.telegram_id) : null
          };

      const response = { data: await (isLogin ? login(payload) : register(payload)) };
      
      toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!');
      
      onLogin({
        user_id: response.data.user_id,
        name: response.data.name,
        token: response.data.access_token
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'linear-gradient(135deg, #e0f7fa 0%, #f1f8e9 100%)' }}>
      <Card className="w-full max-w-md shadow-2xl border-0" data-testid="auth-card">
        <CardHeader className="space-y-4 text-center pb-8">
          <div className="flex justify-center mb-4">
            <div className="bg-gradient-to-br from-teal-500 to-cyan-600 p-4 rounded-2xl shadow-lg" data-testid="logo-container">
              <TrendingUp className="w-12 h-12 text-white" />
            </div>
          </div>
          <CardTitle className="text-3xl sm:text-4xl font-bold" style={{ fontFamily: 'Space Grotesk, sans-serif' }} data-testid="auth-title">
            Stock Monitor
          </CardTitle>
          <CardDescription className="text-base" data-testid="auth-description">
            {isLogin ? 'Sign in to track your stocks' : 'Create your account to get started'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4" data-testid="auth-form">
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="name">Name</label>
                <Input
                  id="name"
                  data-testid="input-name"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required={!isLogin}
                  className="h-11"
                />
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="email">Email</label>
              <Input
                id="email"
                data-testid="input-email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                className="h-11"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="password">Password</label>
              <Input
                id="password"
                data-testid="input-password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                className="h-11"
              />
            </div>
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="telegram">Telegram ID (Optional)</label>
                <Input
                  id="telegram"
                  data-testid="input-telegram"
                  type="number"
                  placeholder="123456789"
                  value={formData.telegram_id}
                  onChange={(e) => setFormData({ ...formData, telegram_id: e.target.value })}
                  className="h-11"
                />
              </div>
            )}
            <Button 
              type="submit" 
              className="w-full h-11 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white font-medium shadow-lg transition-all duration-200 hover:shadow-xl"
              disabled={loading}
              data-testid="submit-button"
            >
              {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-teal-600 hover:text-teal-700 font-medium transition-colors"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
