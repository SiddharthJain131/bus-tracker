import React, { useState, useEffect } from 'react';
import { RefreshCw, Database, AlertCircle, CheckCircle2, Clock, HardDrive, Download, Play, Shield, XCircle, RotateCcw, ChevronRight, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
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
  const [restoreState, setRestoreState] = useState({ stage: null, progress: 0 }); // 'validating', 'restoring', 'success', 'error'
  const [restoreDialog, setRestoreDialog] = useState({ open: false, backup: null });
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

  const initiateRestore = (backup) => {
    setRestoreDialog({ open: true, backup });
  };

  const cancelRestore = () => {
    if (!isRestoring) {
      setRestoreDialog({ open: false, backup: null });
      setRestoreState({ stage: null, progress: 0 });
    }
  };

  const confirmRestore = async () => {
    if (!restoreDialog.backup) return;
    
    setIsRestoring(true);
    
    try {
      // Stage 1: Validating backup
      setRestoreState({ stage: 'validating', progress: 20 });
      await new Promise(resolve => setTimeout(resolve, 800)); // Simulate validation
      
      // Stage 2: Restoring data
      setRestoreState({ stage: 'restoring', progress: 40 });
      
      const response = await axios.post(
        `${BACKEND_URL}/api/admin/backups/restore/${restoreDialog.backup.backup_id}`,
        {},
        { withCredentials: true }
      );

      // Stage 3: Finalizing
      setRestoreState({ stage: 'restoring', progress: 80 });
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Success
      setRestoreState({ stage: 'success', progress: 100 });
      
      toast({
        title: '✅ Restore Successful',
        description: `Restored ${response.data.restored_collections?.length || 0} collection(s) from ${response.data.backup_type} backup`,
        variant: 'default',
        duration: 5000
      });

      // Close dialog after showing success briefly
      setTimeout(() => {
        setRestoreDialog({ open: false, backup: null });
        setRestoreState({ stage: null, progress: 0 });
        
        // Refresh data
        fetchBackupData();
        
        // Optionally refresh entire page after restore
        toast({
          title: 'Page Refreshing',
          description: 'Reloading to reflect restored data...',
          duration: 2000
        });
        setTimeout(() => window.location.reload(), 2500);
      }, 1500);
      
    } catch (error) {
      console.error('Restore failed:', error);
      setRestoreState({ stage: 'error', progress: 0 });
      
      toast({
        title: '❌ Restore Failed',
        description: error.response?.data?.detail || 'Failed to restore backup. Data remains unchanged.',
        variant: 'destructive',
        duration: 7000
      });
      
      // Keep dialog open to show error
      setTimeout(() => {
        setRestoreDialog({ open: false, backup: null });
        setRestoreState({ stage: null, progress: 0 });
      }, 3000);
    } finally {
      setIsRestoring(false);
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

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const kb = bytes / 1024;
    const mb = kb / 1024;
    if (mb >= 1) return `${mb.toFixed(2)} MB`;
    return `${kb.toFixed(2)} KB`;
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
          <h2 className="text-3xl font-bold text-admin-primary">Backup Management</h2>
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
            className="bg-admin-primary hover:bg-admin-hover text-white"
          >
            <Play className={`h-4 w-4 mr-2 ${isTriggering ? 'animate-pulse' : ''}`} />
            {isTriggering ? 'Running...' : 'Run Backup Now'}
          </Button>
        </div>
      </div>

      {/* Overall Health Card */}
      {health && (
        <Card className="dashboard-card admin-accent-border border-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-admin-primary" />
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
                <Card key={backup.backup_id} className={backup.is_valid ? 'border hover:shadow-md transition-shadow' : 'border-2 border-red-200 hover:shadow-md transition-shadow'}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2 flex-1 min-w-0">
                        {/* Header Row */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-semibold text-gray-900 text-sm">{backup.filename}</h4>
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
                            <Badge variant="secondary" className="bg-blue-100 text-blue-800">Latest</Badge>
                          )}
                        </div>
                        
                        {/* Directory with horizontal scroll */}
                        <div className="relative group">
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <HardDrive className="h-3 w-3 flex-shrink-0" />
                            <div 
                              className="overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400 pb-1"
                              role="region"
                              aria-label="Backup directory path"
                              tabIndex={0}
                            >
                              <code className="bg-gray-50 px-2 py-1 rounded text-xs whitespace-nowrap">
                                {backup.directory || '/app/backend/backups'}
                              </code>
                            </div>
                          </div>
                          {/* Scroll indicator */}
                          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        
                        {/* Metadata Row */}
                        <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                          <span className="flex items-center gap-1" title={`Created: ${formatDate(backup.timestamp)}`}>
                            <Clock className="h-3 w-3" />
                            {formatDate(backup.timestamp)}
                          </span>
                          <span className="flex items-center gap-1" title="File size">
                            <HardDrive className="h-3 w-3" />
                            {backup.size_mb} MB
                          </span>
                          <span title="Backup age">Age: {backup.age_days}d</span>
                        </div>
                        
                        {/* Checksum */}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Shield className="h-3 w-3 flex-shrink-0" />
                          <span className="font-medium">Integrity:</span>
                          <code className="bg-gray-50 px-2 py-0.5 rounded text-xs truncate" title={backup.checksum}>
                            {backup.checksum?.substring(0, 16)}...
                          </code>
                        </div>
                        
                        {/* Collections badges */}
                        <div className="flex flex-wrap gap-2 pt-1">
                          {Object.entries(backup.collections || {}).map(([name, count]) => (
                            <Badge key={name} variant="outline" className="text-xs font-normal">
                              {name}: {count}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      {/* Action Button */}
                      <div className="flex-shrink-0">
                        <Button
                          onClick={() => initiateRestore(backup)}
                          disabled={!backup.is_valid || isRestoring}
                          variant={backup.is_valid ? "default" : "secondary"}
                          size="sm"
                          className={backup.is_valid ? "bg-blue-600 hover:bg-blue-700" : ""}
                          title={backup.is_valid ? "Restore this backup" : "Cannot restore invalid backup"}
                        >
                          <RotateCcw className="h-4 w-4 mr-2" />
                          Restore
                        </Button>
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
                <Card key={backup.backup_id} className={backup.is_valid ? 'border hover:shadow-md transition-shadow' : 'border-2 border-red-200 hover:shadow-md transition-shadow'}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-2 flex-1 min-w-0">
                        {/* Header Row */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-semibold text-gray-900 text-sm">{backup.filename}</h4>
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
                            <Badge variant="secondary" className="bg-blue-100 text-blue-800">Latest</Badge>
                          )}
                        </div>
                        
                        {/* Directory with horizontal scroll */}
                        <div className="relative group">
                          <div className="flex items-center gap-2 text-xs text-gray-500">
                            <HardDrive className="h-3 w-3 flex-shrink-0" />
                            <div 
                              className="overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400 pb-1"
                              role="region"
                              aria-label="Backup directory path"
                              tabIndex={0}
                            >
                              <code className="bg-gray-50 px-2 py-1 rounded text-xs whitespace-nowrap">
                                {backup.directory || '/app/backend/backups/attendance'}
                              </code>
                            </div>
                          </div>
                          {/* Scroll indicator */}
                          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        
                        {/* Metadata Row */}
                        <div className="flex items-center gap-4 text-xs text-gray-600 flex-wrap">
                          <span className="flex items-center gap-1" title={`Created: ${formatDate(backup.timestamp)}`}>
                            <Clock className="h-3 w-3" />
                            {formatDate(backup.timestamp)}
                          </span>
                          <span className="flex items-center gap-1" title="File size">
                            <HardDrive className="h-3 w-3" />
                            {backup.size_mb} MB
                          </span>
                          <span title="Backup age">Age: {backup.age_days}d</span>
                        </div>
                        
                        {/* Checksum */}
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Shield className="h-3 w-3 flex-shrink-0" />
                          <span className="font-medium">Integrity:</span>
                          <code className="bg-gray-50 px-2 py-0.5 rounded text-xs truncate" title={backup.checksum}>
                            {backup.checksum?.substring(0, 16)}...
                          </code>
                        </div>
                        
                        {/* Collections badges */}
                        <div className="flex flex-wrap gap-2 pt-1">
                          {Object.entries(backup.collections || {}).map(([name, count]) => (
                            <Badge key={name} variant="outline" className="text-xs font-normal">
                              {name}: {count}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      {/* Action Button */}
                      <div className="flex-shrink-0">
                        <Button
                          onClick={() => initiateRestore(backup)}
                          disabled={!backup.is_valid || isRestoring}
                          variant={backup.is_valid ? "default" : "secondary"}
                          size="sm"
                          className={backup.is_valid ? "bg-blue-600 hover:bg-blue-700" : ""}
                          title={backup.is_valid ? "Restore this backup" : "Cannot restore invalid backup"}
                        >
                          <RotateCcw className="h-4 w-4 mr-2" />
                          Restore
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Restore Confirmation Dialog with Progress */}
      <Dialog open={restoreDialog.open} onOpenChange={(open) => !isRestoring && cancelRestore()}>
        <DialogContent className="sm:max-w-[500px]" onPointerDownOutside={(e) => isRestoring && e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              {restoreState.stage === 'success' ? (
                <>
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                  Restore Complete
                </>
              ) : restoreState.stage === 'error' ? (
                <>
                  <XCircle className="h-6 w-6 text-red-600" />
                  Restore Failed
                </>
              ) : (
                <>
                  <AlertTriangle className="h-6 w-6 text-yellow-600" />
                  Confirm Restore
                </>
              )}
            </DialogTitle>
            <DialogDescription>
              {restoreState.stage === 'success' ? (
                "Backup has been successfully restored. The page will refresh to reflect changes."
              ) : restoreState.stage === 'error' ? (
                "The restore operation failed. Your current data remains unchanged."
              ) : (
                "This action will overwrite your current database with the selected backup."
              )}
            </DialogDescription>
          </DialogHeader>

          {restoreDialog.backup && (
            <div className="space-y-4 py-4">
              {/* Backup Details */}
              {!restoreState.stage && (
                <Card className="bg-gray-50 border-gray-200">
                  <CardContent className="p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Backup File:</span>
                      <code className="text-xs bg-white px-2 py-1 rounded border">{restoreDialog.backup.filename}</code>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Created:</span>
                      <span className="text-sm text-gray-600">{formatDate(restoreDialog.backup.timestamp)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Size:</span>
                      <span className="text-sm text-gray-600">{restoreDialog.backup.size_mb} MB</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Collections:</span>
                      <span className="text-sm text-gray-600">
                        {Object.keys(restoreDialog.backup.collections || {}).length} collection(s)
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Progress Indicator */}
              {(restoreState.stage === 'validating' || restoreState.stage === 'restoring') && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {restoreState.stage === 'validating' ? 'Validating backup...' : 'Restoring data...'}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {restoreState.stage === 'validating' 
                          ? 'Verifying backup integrity and compatibility'
                          : 'Writing data to database collections'}
                      </p>
                    </div>
                  </div>
                  <Progress value={restoreState.progress} className="h-2" />
                  <p className="text-xs text-gray-500 text-center">
                    {restoreState.progress}% complete
                  </p>
                </div>
              )}

              {/* Success Message */}
              {restoreState.stage === 'success' && (
                <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-green-900">
                      Database restored successfully
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      All data has been restored from the backup. The system will refresh momentarily.
                    </p>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {restoreState.stage === 'error' && (
                <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <XCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-red-900">
                      Restore operation failed
                    </p>
                    <p className="text-xs text-red-700 mt-1">
                      The backup could not be restored. Your current data remains unchanged and safe.
                    </p>
                  </div>
                </div>
              )}

              {/* Warning Message */}
              {!restoreState.stage && (
                <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-900">
                      Warning: This action cannot be undone
                    </p>
                    <p className="text-xs text-yellow-700 mt-1">
                      Current data will be replaced with backup data. Consider creating a backup of your current state first.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            {!restoreState.stage ? (
              <>
                <Button
                  variant="outline"
                  onClick={cancelRestore}
                  disabled={isRestoring}
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmRestore}
                  disabled={isRestoring}
                  className="bg-red-600 hover:bg-red-700"
                >
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Confirm Restore
                </Button>
              </>
            ) : restoreState.stage === 'success' || restoreState.stage === 'error' ? (
              <Button
                variant="outline"
                onClick={cancelRestore}
              >
                Close
              </Button>
            ) : null}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BackupManagement;
