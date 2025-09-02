import React from 'react';
import { useAppStore } from '@/stores/appStore';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { 
  Menu, 
  X, 
  Home, 
  Upload, 
  MessageSquare, 
  FileText,
  Plane
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { sidebarOpen, setSidebarOpen, currentView, setCurrentView } = useAppStore();

  const navigation = [
    { name: 'Dashboard', icon: Home, view: 'dashboard' as const },
    { name: 'Upload Reports', icon: Upload, view: 'upload' as const },
    { name: 'Query System', icon: MessageSquare, view: 'query' as const },
    { name: 'Reports', icon: FileText, view: 'reports' as const },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transform transition-transform duration-300 ease-in-out",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center space-x-2">
            <Plane className="h-6 w-6 text-primary" />
            <h1 className="text-lg font-semibold">Boeing ATA System</h1>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <nav className="p-4 space-y-2">
          {navigation.map((item) => (
            <Button
              key={item.name}
              variant={currentView === item.view ? "default" : "ghost"}
              className="w-full justify-start"
              onClick={() => setCurrentView(item.view)}
            >
              <item.icon className="mr-2 h-4 w-4" />
              {item.name}
            </Button>
          ))}
        </nav>

        <div className="absolute bottom-4 left-4 right-4">
          <div className="text-xs text-muted-foreground">
            <p>Boeing Aircraft Maintenance</p>
            <p>Report Management System</p>
            <p className="mt-2 font-mono">v1.0.0</p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className={cn(
        "transition-all duration-300 ease-in-out",
        sidebarOpen ? "lg:ml-64" : "ml-0"
      )}>
        {/* Top bar */}
        <header className="bg-card border-b border-border px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu className="h-4 w-4" />
            </Button>
            <h2 className="text-xl font-semibold capitalize">
              {currentView === 'dashboard' ? 'Dashboard' : 
               currentView === 'upload' ? 'Upload Reports' :
               currentView === 'query' ? 'Query System' : 'Reports'}
            </h2>
          </div>

          <div className="flex items-center space-x-2">
            <div className="text-sm text-muted-foreground">
              ATA Spec 100 | iSpec 2200 | RAG Pipeline
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;
