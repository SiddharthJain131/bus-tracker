import React, { useState } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { toast } from 'sonner';
import { Bus, Lock, Mail, Sparkles, Shield, Zap } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [shake, setShake] = useState(false);
  const [busIconTransitioning, setBusIconTransitioning] = useState(false);
  const [transitionRole, setTransitionRole] = useState(null);

  const getRoleThemeColor = (role) => {
    switch (role) {
      case 'admin':
        return 'from-indigo-500 to-blue-600';
      case 'teacher':
        return 'from-teal-500 to-emerald-600';
      case 'parent':
        return 'from-amber-500 to-orange-600';
      default:
        return 'from-indigo-500 to-blue-600';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, {
        email,
        password,
      });

      toast.success('Login successful!');
      
      // Start bus icon theme transition animation only
      setTransitionRole(response.data.role);
      setBusIconTransitioning(true);
      
      // Quick smooth transition before navigating (300ms for snappy feel)
      setTimeout(() => {
        onLogin(response.data);
      }, 300);
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
      
      {/* Theme Transition Overlay */}
      {transitioning && (
        <div 
          className={`fixed inset-0 z-50 bg-gradient-to-br ${getRoleThemeColor(transitionRole)} transition-opacity duration-500`}
          style={{
            animation: 'fadeToWhite 600ms ease-in-out forwards'
          }}
        />
      )}

      {/* Two-column layout on larger screens, single column on mobile */}
      <div className="w-full max-w-6xl mx-auto grid lg:grid-cols-2 gap-8 items-center">
        
        {/* Left Column - Informational Side Panel */}
        <div className="hidden lg:block space-y-6 fade-in">
          <div className="relative">
            {/* Decorative geometric shapes */}
            <div className="absolute -top-4 -left-4 w-24 h-24 bg-gradient-to-br from-indigo-400/20 to-blue-400/20 rounded-2xl rotate-12 blur-sm"></div>
            <div className="absolute top-20 right-10 w-16 h-16 bg-gradient-to-br from-cyan-400/20 to-indigo-400/20 rounded-full blur-sm"></div>
            
            <Card className="relative p-8 bg-white/10 backdrop-blur-md border border-white/30 shadow-modern-xl rounded-2xl">
              <div className="space-y-6">
                {/* Project Title */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-white/20 to-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/40">
                    <Bus className="w-7 h-7 text-white drop-shadow-lg" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white drop-shadow-lg">School Bus Tracker</h2>
                    <p className="text-white/80 text-sm font-medium">Next-Gen Student Safety System</p>
                  </div>
                </div>

                {/* Project Summary */}
                <div className="space-y-4 text-white/90">
                  <p className="text-base leading-relaxed">
                    A comprehensive real-time tracking and attendance management system combining RFID technology with AI-powered face recognition for enhanced student safety and parent peace of mind.
                  </p>
                  
                  {/* Feature highlights with icons */}
                  <div className="grid grid-cols-1 gap-3 mt-4">
                    <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg backdrop-blur-sm border border-white/20">
                      <Shield className="w-5 h-5 text-white" />
                      <span className="text-sm font-medium">Dual Authentication System</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg backdrop-blur-sm border border-white/20">
                      <Zap className="w-5 h-5 text-white" />
                      <span className="text-sm font-medium">Real-time GPS Tracking</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 bg-white/10 rounded-lg backdrop-blur-sm border border-white/20">
                      <Sparkles className="w-5 h-5 text-white" />
                      <span className="text-sm font-medium">Instant Parent Notifications</span>
                    </div>
                  </div>
                </div>

                {/* Creator Credit */}
                <div className="mt-6 pt-6 border-t border-white/30">
                  <div className="text-center space-y-2">
                    <p className="text-sm text-white/70 font-medium">Website ideated and developed by</p>
                    <p className="text-lg font-bold text-white drop-shadow">Siddharth Jain</p>
                    <p className="text-sm text-white/60 font-mono">(2022AAPS0253P)</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Right Column - Login Form */}
        <div className="w-full">
          <Card className={`w-full max-w-md mx-auto p-8 bg-gradient-to-br from-white/70 via-white/80 to-white/90 backdrop-blur-lg shadow-modern-xl border border-white/50 fade-in hover:shadow-2xl transition-all duration-300 rounded-2xl ${shake ? 'animate-shake' : ''}`}>
            <div className="text-center mb-8 slide-in-left">
              <div className={`inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-50 via-blue-50 to-indigo-100 animate-gradient rounded-2xl mb-4 shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-300 border-2 border-indigo-200 ${transitioning ? `bg-gradient-to-br ${getRoleThemeColor(transitionRole)}` : ''}`}>
                <Bus className={`w-10 h-10 transition-colors duration-500 ${transitioning ? 'text-white' : 'text-indigo-600'}`} />
              </div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-700 via-indigo-600 to-blue-600 bg-clip-text text-transparent mb-2">
                Welcome Back
              </h1>
              <p className="text-gray-600 text-base font-medium">Sign in to continue</p>
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
                    className="pl-12 h-12 bg-white/90 border-gray-200 focus:border-indigo-400 focus:ring-indigo-400"
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
                    className="pl-12 h-12 bg-white/90 border-gray-200 focus:border-indigo-400 focus:ring-indigo-400"
                  />
                </div>
              </div>

              <Button
                data-testid="login-button"
                type="submit"
                disabled={loading}
                variant="accent"
                className="w-full h-12 text-base font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all duration-300"
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

            <div className="mt-8 p-5 bg-gradient-to-br from-blue-50/80 to-indigo-50/80 backdrop-blur-sm rounded-xl border border-blue-200/50 shadow-sm">
              <p className="text-sm font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                Demo Credentials:
              </p>
              <div className="text-sm text-gray-700 space-y-2">
                <p className="hover:text-blue-700 transition-colors cursor-pointer"><strong className="text-orange-600">Parent:</strong> parent@school.com / password</p>
                <p className="hover:text-green-700 transition-colors cursor-pointer"><strong className="text-teal-600">Teacher:</strong> teacher@school.com / password</p>
                <p className="hover:text-blue-700 transition-colors cursor-pointer"><strong className="text-indigo-600">Admin:</strong> admin@school.com / password</p>
              </div>
            </div>

            {/* Mobile-only creator credit */}
            <div className="lg:hidden mt-6 pt-6 border-t border-gray-200">
              <div className="text-center space-y-1">
                <p className="text-xs text-gray-500">Developed by <strong className="text-gray-700">Siddharth Jain</strong></p>
                <p className="text-xs text-gray-400 font-mono">(2022AAPS0253P)</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
