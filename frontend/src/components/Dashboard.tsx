import React, { useEffect } from 'react';
import { useAppStore } from '@/stores/appStore';
import { reportService } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  FileText, 
  AlertTriangle, 
  Wrench, 
  Plane,
  TrendingUp,
  Clock
} from 'lucide-react';

const Dashboard: React.FC = () => {
  const { 
    reportStats, 
    setReportStats, 
    reportsLoading, 
    setReportsLoading, 
    reportsError, 
    setReportsError 
  } = useAppStore();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setReportsLoading(true);
        setReportsError(null);
        const stats = await reportService.getStats();
        setReportStats(stats);
      } catch (error) {
        setReportsError(error instanceof Error ? error.message : 'Failed to fetch statistics');
        console.error('Failed to fetch stats:', error);
      } finally {
        setReportsLoading(false);
      }
    };

    fetchStats();
  }, [setReportStats, setReportsLoading, setReportsError]);

  if (reportsLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-muted rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-muted rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-muted rounded w-full"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (reportsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center text-destructive">
              <AlertTriangle className="mr-2 h-5 w-5" />
              Error Loading Dashboard
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{reportsError}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const stats = reportStats || {
    total_reports: 0,
    reports_by_ata_chapter: {},
    reports_by_severity: {},
    reports_by_aircraft_model: {},
    safety_critical_count: 0,
    recent_reports_count: 0,
  };

  // Calculate top ATA chapters
  const topATAChapters = Object.entries(stats.reports_by_ata_chapter)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 5);

  // Calculate severity distribution
  const severityData = Object.entries(stats.reports_by_severity);

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Reports</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_reports.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Maintenance reports processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Safety Critical</CardTitle>
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{stats.safety_critical_count}</div>
            <p className="text-xs text-muted-foreground">
              Require immediate attention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aircraft Models</CardTitle>
            <Plane className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(stats.reports_by_aircraft_model).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Different aircraft types
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Reports</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.recent_reports_count}</div>
            <p className="text-xs text-muted-foreground">
              Last 30 days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top ATA Chapters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Wrench className="mr-2 h-5 w-5" />
              Top ATA Chapters
            </CardTitle>
            <CardDescription>
              Most frequently reported maintenance areas
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topATAChapters.length > 0 ? (
                topATAChapters.map(([chapter, count]) => (
                  <div key={chapter} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-xs font-medium">
                        {chapter}
                      </div>
                      <span className="text-sm">ATA Chapter {chapter}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary rounded-full"
                          style={{ 
                            width: `${(count / Math.max(...Object.values(stats.reports_by_ata_chapter))) * 100}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm font-medium w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-muted-foreground text-sm">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Severity Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="mr-2 h-5 w-5" />
              Severity Distribution
            </CardTitle>
            <CardDescription>
              Breakdown of report severity levels
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {severityData.length > 0 ? (
                severityData.map(([severity, count]) => {
                  const severityColors = {
                    critical: 'bg-red-500',
                    major: 'bg-orange-500',
                    moderate: 'bg-yellow-500',
                    minor: 'bg-green-500',
                  };
                  const color = severityColors[severity as keyof typeof severityColors] || 'bg-gray-500';
                  
                  return (
                    <div key={severity} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${color}`} />
                        <span className="text-sm capitalize">{severity}</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 h-2 bg-muted rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full ${color}`}
                            style={{ 
                              width: `${(count / Math.max(...Object.values(stats.reports_by_severity))) * 100}%` 
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8 text-right">{count}</span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <p className="text-muted-foreground text-sm">No data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aircraft Models */}
      {Object.keys(stats.reports_by_aircraft_model).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Plane className="mr-2 h-5 w-5" />
              Aircraft Models
            </CardTitle>
            <CardDescription>
              Reports by aircraft type
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(stats.reports_by_aircraft_model).map(([model, count]) => (
                <div key={model} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <span className="font-medium">{model || 'Unknown'}</span>
                  <span className="text-sm text-muted-foreground">{count} reports</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
