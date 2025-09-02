import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/stores/appStore';
import { reportService } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  FileText, 
  Search, 

  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  Calendar,
  Plane,

  Eye
} from 'lucide-react';
import { cn } from '@/lib/utils';

const Reports: React.FC = () => {
  const {
    reports,
    setReports,
    currentReport,
    setCurrentReport,
    reportsLoading,
    setReportsLoading,
    reportsError,
    setReportsError
  } = useAppStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalReports, setTotalReports] = useState(0);
  const [selectedFilters, setSelectedFilters] = useState({
    ata_chapter: '',
    severity: '',
    aircraft_model: '',
  });

  const reportsPerPage = 20;

  // Load reports
  useEffect(() => {
    const loadReports = async () => {
      try {
        setReportsLoading(true);
        setReportsError(null);

        const skip = (currentPage - 1) * reportsPerPage;
        const result = await reportService.getReports(skip, reportsPerPage);
        
        setReports(result.reports);
        setTotalReports(result.total);
      } catch (error) {
        setReportsError(error instanceof Error ? error.message : 'Failed to load reports');
      } finally {
        setReportsLoading(false);
      }
    };

    loadReports();
  }, [currentPage, setReports, setReportsLoading, setReportsError]);

  // Handle search
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setReportsLoading(true);
      setReportsError(null);

      const result = await reportService.searchReports(
        searchQuery.trim(),
        reportsPerPage,
        0.7,
        selectedFilters
      );
      
      setReports(result.reports);
      setTotalReports(result.total);
      setCurrentPage(1);
    } catch (error) {
      setReportsError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setReportsLoading(false);
    }
  };

  // Handle report selection
  const handleReportClick = async (reportId: string) => {
    try {
      const report = await reportService.getReport(reportId);
      setCurrentReport(report);
    } catch (error) {
      console.error('Failed to load report details:', error);
    }
  };

  // Pagination
  const totalPages = Math.ceil(totalReports / reportsPerPage);
  const canGoPrevious = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'major': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'minor': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (reportsLoading && reports.length === 0) {
    return (
      <div className="space-y-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading reports...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Search className="mr-2 h-5 w-5" />
            Search Reports
          </CardTitle>
          <CardDescription>
            Search through maintenance reports or browse all reports
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex space-x-2">
              <Input
                placeholder="Search reports by content, defects, or maintenance actions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" disabled={reportsLoading}>
                <Search className="h-4 w-4" />
              </Button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-1 block">ATA Chapter</label>
                <select
                  className="w-full h-10 px-3 py-2 text-sm border border-input bg-background rounded-md"
                  value={selectedFilters.ata_chapter}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, ata_chapter: e.target.value }))}
                >
                  <option value="">All Chapters</option>
                  <option value="21">21 - Air Conditioning</option>
                  <option value="27">27 - Flight Controls</option>
                  <option value="32">32 - Landing Gear</option>
                  <option value="52">52 - Doors</option>
                  <option value="53">53 - Fuselage</option>
                  <option value="57">57 - Wings</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">Severity</label>
                <select
                  className="w-full h-10 px-3 py-2 text-sm border border-input bg-background rounded-md"
                  value={selectedFilters.severity}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, severity: e.target.value }))}
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="major">Major</option>
                  <option value="moderate">Moderate</option>
                  <option value="minor">Minor</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">Aircraft Model</label>
                <Input
                  placeholder="e.g., Boeing 737-800"
                  value={selectedFilters.aircraft_model}
                  onChange={(e) => setSelectedFilters(prev => ({ ...prev, aircraft_model: e.target.value }))}
                />
              </div>
            </div>
          </form>

          {reportsError && (
            <div className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive font-medium">Search Error</p>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{reportsError}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reports List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Reports List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center">
                <FileText className="mr-2 h-5 w-5" />
                Reports ({totalReports})
              </span>
              {reportsLoading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="space-y-0 max-h-96 overflow-y-auto">
              {reports.length === 0 ? (
                <div className="p-6 text-center text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No reports found</p>
                  <p className="text-sm">Try adjusting your search or filters</p>
                </div>
              ) : (
                reports.map((report) => (
                  <div
                    key={report.id}
                    className={cn(
                      "p-4 border-b border-border cursor-pointer hover:bg-muted/50 transition-colors",
                      currentReport?.id === report.id && "bg-muted"
                    )}
                    onClick={() => handleReportClick(report.id)}
                  >
                    <div className="flex items-start justify-between space-x-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-medium truncate">
                            Report {report.id.slice(0, 8)}...
                          </span>
                          {report.ata_chapter && (
                            <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                              ATA {report.ata_chapter}
                            </span>
                          )}
                          {report.safety_critical && (
                            <AlertTriangle className="h-4 w-4 text-destructive" />
                          )}
                        </div>
                        
                        <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                          {report.report_text}
                        </p>
                        
                        <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                          {report.aircraft_model && (
                            <span className="flex items-center">
                              <Plane className="h-3 w-3 mr-1" />
                              {report.aircraft_model}
                            </span>
                          )}
                          {report.severity && (
                            <span className={cn(
                              "px-2 py-1 rounded border text-xs",
                              getSeverityColor(report.severity)
                            )}>
                              {report.severity}
                            </span>
                          )}
                          <span className="flex items-center">
                            <Calendar className="h-3 w-3 mr-1" />
                            {new Date(report.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="p-4 border-t border-border flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Page {currentPage} of {totalPages}
                </p>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => prev - 1)}
                    disabled={!canGoPrevious || reportsLoading}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(prev => prev + 1)}
                    disabled={!canGoNext || reportsLoading}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Report Details */}
        <Card>
          <CardHeader>
            <CardTitle>Report Details</CardTitle>
            <CardDescription>
              {currentReport ? `Report ${currentReport.id.slice(0, 8)}...` : 'Select a report to view details'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {currentReport ? (
              <div className="space-y-4">
                {/* Report metadata */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-lg">
                  <div>
                    <p className="text-xs text-muted-foreground">Aircraft Model</p>
                    <p className="font-medium">{currentReport.aircraft_model || 'Not specified'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">ATA Chapter</p>
                    <p className="font-medium">
                      {currentReport.ata_chapter ? `${currentReport.ata_chapter} - ${currentReport.ata_chapter_name || 'Unknown'}` : 'Not classified'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Severity</p>
                    <span className={cn(
                      "inline-block px-2 py-1 rounded border text-xs font-medium",
                      getSeverityColor(currentReport.severity || 'unknown')
                    )}>
                      {currentReport.severity || 'Unknown'}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Safety Critical</p>
                    <p className="font-medium flex items-center">
                      {currentReport.safety_critical ? (
                        <>
                          <AlertTriangle className="h-4 w-4 text-destructive mr-1" />
                          Yes
                        </>
                      ) : (
                        'No'
                      )}
                    </p>
                  </div>
                </div>

                {/* Report text */}
                <div>
                  <h4 className="font-medium mb-2">Report Text</h4>
                  <div className="p-4 bg-muted/30 rounded-lg">
                    <p className="text-sm whitespace-pre-wrap">{currentReport.report_text}</p>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="text-xs text-muted-foreground space-y-1">
                  <p>Created: {new Date(currentReport.created_at).toLocaleString()}</p>
                  <p>Updated: {new Date(currentReport.updated_at).toLocaleString()}</p>
                </div>
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a report from the list to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Reports;
