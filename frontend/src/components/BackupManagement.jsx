import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, AlertCircle, CheckCircle2, Clock, HardDrive, Download, Play, Shield, XCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useToast } from '../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const BackupManagement = () => {
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const [mainBackups, setMainBackups] = useState([]);
  const [attendanceBackups, setAttendanceBackups] = useState([]);
  const [isTriggering, setIsTriggering] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreConfirm, setRestoreConfirm] = useState(null);
  const { toast } = useToast();

  // Fetch backup health and list on mount
  useEffect(() => {
    fetchBackupData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchBackupData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchBackupData = async () => {
    setLoading(true);
    try {
      // Fetch health
      const healthResponse = await axios.get(`${BACKEND_URL}/api/admin/backups/health`, {
        withCredentials: true
      });
      setHealth(healthResponse.data);

      // Fetch backup lists
      const listResponse = await axios.get(`${BACKEND_URL}/api/admin/backups/list?backup_type=both`, {
        withCredentials: true
      });
      setMainBackups(listResponse.data.main || []);
      setAttendanceBackups(listResponse.data.attendance || []);
    } catch (error) {
      console.error('Failed to fetch backup data:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch backup information',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const triggerBackup = async (type) => {
    setIsTriggering(true);
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/backups/trigger?backup_type=${type}`,
        {},
        { withCredentials: true }
      );

      toast({
        title: 'Backup Triggered',
        description: `${type === 'both' ? 'Main and attendance' : type.charAt(0).toUpperCase() + type.slice(1)} backup completed successfully`,
        variant: 'default'
      });

      // Refresh data
      await fetchBackupData();
    } catch (error) {
      console.error('Backup trigger failed:', error);
      toast({
        title: 'Backup Failed',
        description: error.response?.data?.detail || 'Failed to trigger backup',
        variant: 'destructive'
      });
    } finally {
      setIsTriggering(false);
    }
  };

  const getHealthBadge = (healthStatus) => {
    const statusConfig = {
      healthy: { label: 'Healthy', variant: 'default', icon: CheckCircle2, color: 'text-green-600' },
      caution: { label: 'Caution', variant: 'secondary', icon: AlertCircle, color: 'text-yellow-600' },
      warning: { label: 'Warning', variant: 'secondary', icon: AlertCircle, color: 'text-orange-600' },
      critical: { label: 'Critical', variant: 'destructive', icon: XCircle, color: 'text-red-600' }
    };

    const config = statusConfig[healthStatus] || statusConfig.critical;
    const Icon = config.icon;

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {config.label}
      </Badge>
    );
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAgeString = (hours) => {
    if (hours < 1) return `${Math.round(hours * 60)} minutes ago`;
    if (hours < 24) return `${Math.round(hours)} hours ago`;
    return `${Math.round(hours / 24)} days ago`;
  };

  if (loading && !health) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header with Manual Trigger */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Backup Management</h2>
          <p className="text-gray-600 mt-1">Monitor and manage system backups</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => fetchBackupData()}
            disabled={loading}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            onClick={() => triggerBackup('both')}
            disabled={isTriggering}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Play className={`h-4 w-4 mr-2 ${isTriggering ? 'animate-pulse' : ''}`} />
            {isTriggering ? 'Running...' : 'Run Backup Now'}
          </Button>
        </div>
      </div>

      {/* Overall Health Card */}
      {health && (
        <Card className="border-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-600" />
                Overall Backup Health
              </CardTitle>
              {getHealthBadge(health.overall_health)}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Main Backup Status */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Database className="h-4 w-4" />
                  Main Backup
                </div>
                <div className="pl-6 space-y-1">
                  <div className="flex items-center gap-2">
                    {getHealthBadge(health.main_backup.health)}
                    {health.main_backup.last_backup && (
                      <span className="text-xs text-gray-500">
                        {formatAgeString(health.main_backup.last_backup.age_hours)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">{health.main_backup.message}</p>
                </div>
              </div>

              {/* Attendance Backup Status */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <Clock className="h-4 w-4" />
                  Attendance Backup
                </div>
                <div className="pl-6 space-y-1">
                  <div className="flex items-center gap-2">
                    {getHealthBadge(health.attendance_backup.health)}
                    {health.attendance_backup.last_backup && (
                      <span className="text-xs text-gray-500">
                        {formatAgeString(health.attendance_backup.last_backup.age_hours)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">{health.attendance_backup.message}</p>
                </div>
              </div>

              {/* Storage Info */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <HardDrive className="h-4 w-4" />
                  Storage
                </div>
                <div className="pl-6 space-y-1">
                  <div className="flex items-center gap-2">
                    {health.storage.has_sufficient_space ? (
                      <Badge variant="default" className="bg-green-100 text-green-800">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Sufficient
                      </Badge>
                    ) : (
                      <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        Low Space
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-gray-600">
                    {health.storage.free_mb.toFixed(2)} MB free
                  </p>
                  <p className="text-xs text-gray-500">
                    Min: {health.storage.minimum_required_mb} MB
                  </p>
                </div>
              </div>
            </div>

            {/* Configuration Info */}
            <div className="mt-4 pt-4 border-t">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Retention Limit:</span> {health.configuration.backup_limit} backups
                </div>
                <div>
                  <span className="font-medium">Retention Period:</span> {health.configuration.retention_days} days
                </div>
                <div className="md:col-span-1 col-span-2">
                  <span className="font-medium">Directory:</span> <code className="bg-gray-100 px-1 rounded">{health.configuration.backup_directory}</code>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Backup History Tabs */}
      <Tabs defaultValue="main" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="main">
            Main Backups ({mainBackups.length})
          </TabsTrigger>
          <TabsTrigger value="attendance">
            Attendance Backups ({attendanceBackups.length})
          </TabsTrigger>
        </TabsList>

        {/* Main Backups Tab */}
        <TabsContent value="main" className="space-y-4">
          {mainBackups.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-8">
                <Database className="h-12 w-12 text-gray-400 mb-2" />
                <p className="text-gray-600">No main backups found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {mainBackups.map((backup) => (
                <Card key={backup.backup_id} className={backup.is_valid ? 'border' : 'border-2 border-red-200'}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{backup.filename}</h4>
                          {backup.is_valid ? (
                            <Badge variant="default" className="bg-green-100 text-green-800">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Valid
                            </Badge>
                          ) : (
                            <Badge variant="destructive">
                              <XCircle className="h-3 w-3 mr-1" />
                              Invalid
                            </Badge>
                          )}
                          {backup.age_days === 0 && (
                            <Badge variant="secondary">Latest</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(backup.timestamp)}
                          </span>
                          <span>Size: {backup.size_mb} MB</span>
                          <span>Age: {backup.age_days} days</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Shield className="h-3 w-3" />
                          Checksum: <code className="bg-gray-100 px-1 rounded">{backup.checksum}</code>
                        </div>
                        {/* Collections count */}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {Object.entries(backup.collections || {}).map(([name, count]) => (
                            <Badge key={name} variant="outline" className="text-xs">
                              {name}: {count}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Attendance Backups Tab */}
        <TabsContent value="attendance" className="space-y-4">
          {attendanceBackups.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center p-8">
                <Clock className="h-12 w-12 text-gray-400 mb-2" />
                <p className="text-gray-600">No attendance backups found</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {attendanceBackups.map((backup) => (
                <Card key={backup.backup_id} className={backup.is_valid ? 'border' : 'border-2 border-red-200'}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-gray-900">{backup.filename}</h4>
                          {backup.is_valid ? (
                            <Badge variant="default" className="bg-green-100 text-green-800">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Valid
                            </Badge>
                          ) : (
                            <Badge variant="destructive">
                              <XCircle className="h-3 w-3 mr-1" />
                              Invalid
                            </Badge>
                          )}
                          {backup.age_days === 0 && (
                            <Badge variant="secondary">Latest</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-600">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(backup.timestamp)}
                          </span>
                          <span>Size: {backup.size_mb} MB</span>
                          <span>Age: {backup.age_days} days</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Shield className="h-3 w-3" />
                          Checksum: <code className="bg-gray-100 px-1 rounded">{backup.checksum}</code>
                        </div>
                        {/* Collections count */}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {Object.entries(backup.collections || {}).map(([name, count]) => (
                            <Badge key={name} variant="outline" className="text-xs">
                              {name}: {count}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BackupManagement;
