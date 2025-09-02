import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useAppStore } from '@/stores/appStore';
import { reportService } from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Upload as UploadIcon, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  X,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';

const Upload: React.FC = () => {
  const {
    uploadProgress,
    uploadLoading,
    uploadError,
    setUploadProgress,
    setUploadLoading,
    setUploadError,
    resetUpload
  } = useAppStore();

  const [singleReportText, setSingleReportText] = useState('');
  const [aircraftModel, setAircraftModel] = useState('');
  const [uploadResults, setUploadResults] = useState<{
    processed: number;
    errors: number;
    message: string;
  } | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    try {
      setUploadLoading(true);
      setUploadError(null);
      setUploadProgress(0);
      setUploadResults(null);

      // Simulate progress updates
      let currentProgress = 0;
      const progressInterval = setInterval(() => {
        currentProgress = Math.min(currentProgress + 10, 90);
        setUploadProgress(currentProgress);
      }, 200);

      const result = await reportService.uploadReports(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadResults(result);
      
      // Reset progress after a delay
      setTimeout(() => {
        setUploadProgress(0);
      }, 2000);

    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploadLoading(false);
    }
  }, [setUploadLoading, setUploadError, setUploadProgress, setUploadResults]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
    },
    multiple: false,
    disabled: uploadLoading,
  });

  const handleSingleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleReportText.trim()) return;

    try {
      setUploadLoading(true);
      setUploadError(null);

      const result = await reportService.ingestReport(
        singleReportText.trim(),
        aircraftModel.trim() || undefined
      );

      setUploadResults({
        processed: 1,
        errors: 0,
        message: `Report processed successfully with ID: ${result.report_id}`,
      });

      // Clear form
      setSingleReportText('');
      setAircraftModel('');

    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Failed to process report');
    } finally {
      setUploadLoading(false);
    }
  };

  const clearResults = () => {
    setUploadResults(null);
    resetUpload();
  };

  return (
    <div className="space-y-6">
      {/* File Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <UploadIcon className="mr-2 h-5 w-5" />
            Batch Upload
          </CardTitle>
          <CardDescription>
            Upload a text file containing multiple maintenance reports (one per line)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25",
              uploadLoading && "cursor-not-allowed opacity-50"
            )}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center space-y-4">
              <div className={cn(
                "w-16 h-16 rounded-full flex items-center justify-center",
                isDragActive ? "bg-primary/10" : "bg-muted"
              )}>
                {uploadLoading ? (
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                ) : (
                  <FileText className="h-8 w-8 text-muted-foreground" />
                )}
              </div>
              
              {uploadLoading ? (
                <div className="space-y-2">
                  <p className="text-lg font-medium">Processing...</p>
                  <div className="w-64 h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground">{uploadProgress}% complete</p>
                </div>
              ) : isDragActive ? (
                <p className="text-lg font-medium text-primary">Drop the file here...</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-lg font-medium">
                    Drag & drop a file here, or click to select
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Supports .txt and .csv files
                  </p>
                </div>
              )}
            </div>
          </div>

          {uploadError && (
            <div className="mt-4 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <p className="text-sm text-destructive font-medium">Upload Error</p>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{uploadError}</p>
            </div>
          )}

          {uploadResults && (
            <div className="mt-4 p-4 rounded-lg bg-green-50 border border-green-200 dark:bg-green-950 dark:border-green-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <p className="text-sm text-green-800 dark:text-green-200 font-medium">
                    Upload Complete
                  </p>
                </div>
                <Button variant="ghost" size="sm" onClick={clearResults}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <div className="mt-2 text-sm text-green-700 dark:text-green-300">
                <p>{uploadResults.message}</p>
                <p>Processed: {uploadResults.processed} reports</p>
                {uploadResults.errors > 0 && (
                  <p>Errors: {uploadResults.errors} reports</p>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Single Report Entry */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="mr-2 h-5 w-5" />
            Single Report Entry
          </CardTitle>
          <CardDescription>
            Enter a single maintenance report for immediate processing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSingleReportSubmit} className="space-y-4">
            <div>
              <label htmlFor="aircraft-model" className="text-sm font-medium mb-2 block">
                Aircraft Model (Optional)
              </label>
              <Input
                id="aircraft-model"
                placeholder="e.g., Boeing 737-800"
                value={aircraftModel}
                onChange={(e) => setAircraftModel(e.target.value)}
                disabled={uploadLoading}
              />
            </div>

            <div>
              <label htmlFor="report-text" className="text-sm font-medium mb-2 block">
                Maintenance Report Text *
              </label>
              <textarea
                id="report-text"
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                placeholder="Enter maintenance report details here..."
                value={singleReportText}
                onChange={(e) => setSingleReportText(e.target.value)}
                disabled={uploadLoading}
                required
              />
            </div>

            <Button 
              type="submit" 
              disabled={!singleReportText.trim() || uploadLoading}
              className="w-full"
            >
              {uploadLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <UploadIcon className="mr-2 h-4 w-4" />
                  Process Report
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Upload Guidelines */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Guidelines</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">File Format Requirements:</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Text files (.txt) or CSV files (.csv)</li>
              <li>• One maintenance report per line</li>
              <li>• Maximum file size: 10MB</li>
              <li>• UTF-8 encoding recommended</li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-2">Report Content:</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Include aircraft model when available</li>
              <li>• Describe maintenance actions performed</li>
              <li>• Mention any defects or issues found</li>
              <li>• Reference ATA chapters when applicable</li>
            </ul>
          </div>

          <div>
            <h4 className="font-medium mb-2">Processing:</h4>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• Reports are automatically classified by ATA chapter</li>
              <li>• Defect types and severity are detected</li>
              <li>• Vector embeddings are generated for search</li>
              <li>• Safety-critical issues are flagged</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Upload;
