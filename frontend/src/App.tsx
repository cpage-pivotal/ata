
import { useAppStore } from '@/stores/appStore';
import Layout from '@/components/Layout';
import Dashboard from '@/components/Dashboard';
import Upload from '@/components/Upload';
import Query from '@/components/Query';
import Reports from '@/components/Reports';

function App() {
  const { currentView } = useAppStore();

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'upload':
        return <Upload />;
      case 'query':
        return <Query />;
      case 'reports':
        return <Reports />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout>
      {renderCurrentView()}
    </Layout>
  );
}

export default App;