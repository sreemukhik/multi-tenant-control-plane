"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var react_query_1 = require("@tanstack/react-query");
var react_router_dom_1 = require("react-router-dom");
var StoreList_1 = require("./components/StoreList");
var StoreDetail_1 = require("./components/StoreDetail");
var queryClient = new react_query_1.QueryClient();
function App() {
    return (<react_query_1.QueryClientProvider client={queryClient}>
      <react_router_dom_1.BrowserRouter>
        <div className="min-h-screen bg-background font-sans antialiased">
          <header className="border-b">
            <div className="container flex h-16 items-center px-4">
              <react_router_dom_1.Link to="/" className="text-lg font-bold mr-6">Urumi Platform</react_router_dom_1.Link>
              <nav className="flex items-center space-x-6 text-sm font-medium">
                <react_router_dom_1.Link to="/" className="transition-colors hover:text-foreground/80 text-foreground">Stores</react_router_dom_1.Link>
                <react_router_dom_1.Link to="/settings" className="transition-colors hover:text-foreground/80 text-foreground/60">Settings</react_router_dom_1.Link>
              </nav>
            </div>
          </header>
          <main className="container py-6">
            <react_router_dom_1.Routes>
              <react_router_dom_1.Route path="/" element={<StoreList_1.default />}/>
              <react_router_dom_1.Route path="/stores/:id" element={<StoreDetail_1.default />}/>
            </react_router_dom_1.Routes>
          </main>
        </div>
      </react_router_dom_1.BrowserRouter>
    </react_query_1.QueryClientProvider>);
}
exports.default = App;
