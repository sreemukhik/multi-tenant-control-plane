import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import StoreList from './components/StoreList';
import StoreDetail from './components/StoreDetail';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-background font-sans antialiased">
          <header className="border-b">
            <div className="container flex h-16 items-center px-4">
              <Link to="/" className="text-lg font-bold mr-6">Urumi Platform</Link>
              <nav className="flex items-center space-x-6 text-sm font-medium">
                <Link to="/" className="transition-colors hover:text-foreground/80 text-foreground">Stores</Link>
                <Link to="/settings" className="transition-colors hover:text-foreground/80 text-foreground/60">Settings</Link>
              </nav>
            </div>
          </header>
          <main className="container py-6">
            <Routes>
              <Route path="/" element={<StoreList />} />
              <Route path="/stores/:id" element={<StoreDetail />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
