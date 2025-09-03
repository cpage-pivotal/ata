import axios, { type AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Type definitions
export interface MaintenanceReport {
  id: string;
  report_text: string;
  aircraft_model?: string;
  report_date?: string;
  ata_chapter?: string;
  ata_chapter_name?: string;
  ispec_part?: string;
  defect_type?: string;
  severity?: string;
  safety_critical?: boolean;
  created_at: string;
  updated_at: string;
}

export interface Classification {
  ata_chapter?: string;
  ata_chapter_name?: string;
  defect_types: string[];
  maintenance_actions: string[];
  identified_parts: string[];
  severity: string;
  safety_critical: boolean;
  overall_confidence: number;
  processing_notes?: string[];
}

export interface QueryResponse {
  response: string;
  sources: Array<{
    report_id: string;
    aircraft_model?: string;
    ata_chapter?: string;
    ata_chapter_name?: string;
    similarity_score: number;
    excerpt: string;
    safety_critical: boolean;
    severity: string;
  }>;
  metadata: {
    processing_time_ms: number;
    total_sources_considered: number;
    confidence_score: number;
    query_type: string;
    model_used: string;
  };
}

export interface ReportStats {
  total_reports: number;
  reports_by_ata_chapter: Record<string, number>;
  reports_by_severity: Record<string, number>;
  reports_by_aircraft_model: Record<string, number>;
  safety_critical_count: number;
  recent_reports_count: number;
}

// API Service functions
export const reportService = {
  // Upload multiple reports from file
  uploadReports: async (file: File): Promise<{ message: string; processed: number; errors: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post('/api/reports/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Ingest single report
  ingestReport: async (reportText: string, aircraftModel?: string): Promise<{ report_id: string; classification: Classification }> => {
    const response = await apiClient.post('/api/reports/ingest', {
      report_text: reportText,
      aircraft_model: aircraftModel,
    });
    return response.data;
  },

  // Get all reports with pagination
  getReports: async (skip = 0, limit = 50): Promise<{ reports: MaintenanceReport[]; total: number }> => {
    const response = await apiClient.get('/api/reports/', {
      params: { skip, limit },
    });
    return response.data;
  },

  // Get specific report
  getReport: async (reportId: string): Promise<MaintenanceReport> => {
    const response = await apiClient.get(`/api/reports/${reportId}`);
    return response.data;
  },

  // Get report statistics
  getStats: async (): Promise<ReportStats> => {
    const response = await apiClient.get('/api/reports/stats/summary');
    return response.data;
  },

  // Semantic search
  searchReports: async (
    queryText: string,
    limit = 10,
    similarityThreshold = 0.7,
    filters?: {
      ata_chapter?: string;
      severity?: string;
      aircraft_model?: string;
    }
  ): Promise<{ reports: MaintenanceReport[]; total: number }> => {
    const response = await apiClient.post('/api/reports/search', {
      query_text: queryText,
      limit,
      similarity_threshold: similarityThreshold,
      filters: filters || {},
    });
    return response.data;
  },

  // Classify report text
  classifyReport: async (reportText: string): Promise<Classification> => {
    const response = await apiClient.post('/api/reports/classify', {
      report_text: reportText,
    });
    return response.data;
  },
};

// Fixed queryService in frontend/src/services/api.ts
export const queryService = {
    // Process natural language query - FIXED to use FormData
    processQuery: async (
        queryText: string,
        options?: {
            similarity_threshold?: number;
            temperature?: number;
            ata_chapter?: string;
            max_results?: number;
            include_sources?: boolean;
            query_type?: string;
        }
    ): Promise<QueryResponse> => {
        // Create FormData instead of JSON
        const formData = new FormData();
        formData.append('query_text', queryText);

        // Add optional parameters if provided
        if (options?.max_results !== undefined) {
            formData.append('max_results', options.max_results.toString());
        }
        if (options?.include_sources !== undefined) {
            formData.append('include_sources', options.include_sources.toString());
        }
        if (options?.similarity_threshold !== undefined) {
            formData.append('similarity_threshold', options.similarity_threshold.toString());
        }
        if (options?.temperature !== undefined) {
            formData.append('temperature', options.temperature.toString());
        }
        if (options?.ata_chapter) {
            formData.append('ata_chapter', options.ata_chapter);
        }
        if (options?.query_type) {
            formData.append('query_type', options.query_type);
        }

        const response = await apiClient.post('/api/query', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Submit feedback - ALSO needs to be FormData based on backend
    submitFeedback: async (queryId: string, helpful: boolean, feedbackText?: string): Promise<{ message: string }> => {
        const formData = new FormData();
        formData.append('query_id', queryId);
        formData.append('helpful', helpful.toString());
        if (feedbackText) {
            formData.append('feedback_text', feedbackText);
        }

        const response = await apiClient.post('/api/query/feedback', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // Get query history - this one is fine as-is
    getHistory: async (limit = 20): Promise<Array<{ id: string; query_text: string; response: string; created_at: string }>> => {
        const response = await apiClient.get('/api/query/history', {
            params: { limit },
        });
        return response.data;
    },

    // Get query suggestions - this one is fine as-is
    getSuggestions: async (): Promise<string[]> => {
        const response = await apiClient.get('/api/query/suggestions');
        return response.data;
    },
};

export const healthService = {
  // Basic health check
  checkHealth: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await apiClient.get('/api/health');
    return response.data;
  },

  // Detailed health check
  checkDetailedHealth: async (): Promise<{
    status: string;
    services: Record<string, { status: string; details?: any }>;
    timestamp: string;
  }> => {
    const response = await apiClient.get('/api/health/detailed');
    return response.data;
  },
};
