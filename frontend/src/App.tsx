import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StoreList from './components/StoreList';
import StoreDetail from './components/StoreDetail';
import { Sidebar } from './components/Sidebar';

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
              {/* Simple placeholders to match original menu */}
              <Route path="/observability" element={<div className="text-sm text-muted-foreground">Observability dashboard coming soon.</div>} />
              <Route path="/audit-logs" element={<div className="text-sm text-muted-foreground">Audit logs view coming soon.</div>} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
