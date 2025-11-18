import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { toast } from 'sonner';
import { Bus, Lock, Mail } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password,
      });

      toast.success('Login successful!');
      onLogin(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
      // Trigger shake animation on failed login
      setShake(true);
      setTimeout(() => setShake(false), 200);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 animated-gradient-bg relative overflow-hidden">
      {/* Floating decorative shapes */}
      <div className="absolute top-20 left-10 w-64 h-64 bg-blue-400/10 rounded-full blur-3xl floating-shape" style={{ animationDelay: '0s' }}></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-indigo-400/10 rounded-full blur-3xl floating-shape" style={{ animationDelay: '5s' }}></div>
      <div className="absolute top-1/2 left-1/3 w-48 h-48 bg-cyan-400/10 rounded-full blur-3xl floating-shape" style={{ animationDelay: '10s' }}></div>
      
      <Card className={`w-full max-w-md p-8 bg-white/95 backdrop-blur-xl shadow-modern-xl border-0 fade-in hover:scale-[1.01] transition-transform duration-300 rounded-2xl ${shake ? 'animate-shake' : ''}`}>
        <div className="text-center mb-8 slide-in-left">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-gray-50 via-indigo-50 to-blue-50 animate-gradient rounded-2xl mb-4 shadow-lg hover:shadow-xl transition-shadow duration-300 border-2 border-indigo-100">
            <Bus className="w-10 h-10 text-indigo-600" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-700 via-indigo-600 to-blue-600 bg-clip-text text-transparent mb-2">
            School Bus Tracker
          </h1>
          <p className="text-gray-600 text-base font-medium">RFID + Face Recognition System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5" data-testid="login-form">
          <div className="space-y-2">
            <label className="text-sm font-semibold text-navy">Email</label>
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
              <Input
                data-testid="email-input"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="pl-12 h-12"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-navy">Password</label>
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
              <Input
                data-testid="password-input"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="pl-12 h-12"
              />
            </div>
          </div>

          <Button
            data-testid="login-button"
            type="submit"
            disabled={loading}
            variant="accent"
            className="w-full h-12 text-base font-semibold"
          >
            {loading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="spinner" />
                Logging in...
              </div>
            ) : (
              'Login'
            )}
          </Button>
        </form>

        <div className="mt-8 p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200/50 shadow-sm">
          <p className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
            Demo Credentials:
          </p>
          <div className="text-sm text-gray-700 space-y-2">
            <p className="hover:text-blue-700 transition-colors"><strong className="text-orange-600">Parent:</strong> parent@school.com / password</p>
            <p className="hover:text-green-700 transition-colors"><strong className="text-teal-600">Teacher:</strong> teacher@school.com / password</p>
            <p className="hover:text-blue-700 transition-colors"><strong className="text-indigo-600">Admin:</strong> admin@school.com / password</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
