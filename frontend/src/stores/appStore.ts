import { create } from 'zustand';
import { type MaintenanceReport, type QueryResponse, type ReportStats } from '@/services/api';

interface AppState {
  // Reports state
  reports: MaintenanceReport[];
  currentReport: MaintenanceReport | null;
  reportStats: ReportStats | null;
  reportsLoading: boolean;
  reportsError: string | null;

  // Query state
  queryHistory: Array<{ id: string; query_text: string; response: string; created_at: string }>;
  currentQuery: string;
  currentResponse: QueryResponse | null;
  queryLoading: boolean;
  queryError: string | null;

  // Upload state
  uploadProgress: number;
  uploadLoading: boolean;
  uploadError: string | null;

  // UI state
  sidebarOpen: boolean;
  currentView: 'dashboard' | 'upload' | 'query' | 'reports';

  // Actions
  setReports: (reports: MaintenanceReport[]) => void;
  setCurrentReport: (report: MaintenanceReport | null) => void;
  setReportStats: (stats: ReportStats) => void;
  setReportsLoading: (loading: boolean) => void;
  setReportsError: (error: string | null) => void;

  setQueryHistory: (history: Array<{ id: string; query_text: string; response: string; created_at: string }>) => void;
  setCurrentQuery: (query: string) => void;
  setCurrentResponse: (response: QueryResponse | null) => void;
  setQueryLoading: (loading: boolean) => void;
  setQueryError: (error: string | null) => void;

  setUploadProgress: (progress: number) => void;
  setUploadLoading: (loading: boolean) => void;
  setUploadError: (error: string | null) => void;

  setSidebarOpen: (open: boolean) => void;
  setCurrentView: (view: 'dashboard' | 'upload' | 'query' | 'reports') => void;

  // Reset functions
  resetReports: () => void;
  resetQuery: () => void;
  resetUpload: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  reports: [],
  currentReport: null,
  reportStats: null,
  reportsLoading: false,
  reportsError: null,

  queryHistory: [],
  currentQuery: '',
  currentResponse: null,
  queryLoading: false,
  queryError: null,

  uploadProgress: 0,
  uploadLoading: false,
  uploadError: null,

  sidebarOpen: true,
  currentView: 'dashboard',

  // Actions
  setReports: (reports) => set({ reports }),
  setCurrentReport: (report) => set({ currentReport: report }),
  setReportStats: (stats) => set({ reportStats: stats }),
  setReportsLoading: (loading) => set({ reportsLoading: loading }),
  setReportsError: (error) => set({ reportsError: error }),

  setQueryHistory: (history) => set({ queryHistory: history }),
  setCurrentQuery: (query) => set({ currentQuery: query }),
  setCurrentResponse: (response) => set({ currentResponse: response }),
  setQueryLoading: (loading) => set({ queryLoading: loading }),
  setQueryError: (error) => set({ queryError: error }),

  setUploadProgress: (progress) => set({ uploadProgress: progress }),
  setUploadLoading: (loading) => set({ uploadLoading: loading }),
  setUploadError: (error) => set({ uploadError: error }),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setCurrentView: (view) => set({ currentView: view }),

  // Reset functions
  resetReports: () => set({
    reports: [],
    currentReport: null,
    reportStats: null,
    reportsLoading: false,
    reportsError: null,
  }),

  resetQuery: () => set({
    currentQuery: '',
    currentResponse: null,
    queryLoading: false,
    queryError: null,
  }),

  resetUpload: () => set({
    uploadProgress: 0,
    uploadLoading: false,
    uploadError: null,
  }),
}));
