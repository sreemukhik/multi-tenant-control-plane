import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StoreList from './components/StoreList';
import StoreDetail from './components/StoreDetail';
import { Sidebar } from './components/Sidebar';
import Observability from './components/Observability';
import AuditLogView from './components/AuditLogView';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background text-foreground font-sans antialiased flex">
          <Sidebar />
          <main className="flex-1 px-8 py-8">
            <Routes>
              <Route path="/" element={<StoreList />} />
              <Route path="/stores/:id" element={<StoreDetail />} />
              <Route path="/observability" element={<Observability />} />
              <Route path="/audit-logs" element={<AuditLogView />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
