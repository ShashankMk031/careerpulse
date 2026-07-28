import { lazy, Suspense, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import PageContainer from "./components/layout/PageContainer";
import Footer from "./components/layout/Footer";
import Loading from "./components/common/Loading";
import ErrorBoundary from "./components/common/ErrorBoundary";
import { QUERY_STALE_TIME, QUERY_RETRY_COUNT } from "./constants/query";

// Lazy loaded page components
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Companies = lazy(() => import("./pages/Companies"));
const Skills = lazy(() => import("./pages/Skills"));
const Technology = lazy(() => import("./pages/Technology"));
const Geography = lazy(() => import("./pages/Geography"));
const Salary = lazy(() => import("./pages/Salary"));
const Status = lazy(() => import("./pages/Status"));
const About = lazy(() => import("./pages/About"));
const NotFound = lazy(() => import("./pages/NotFound"));

// Configure React Query default parameters
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: QUERY_RETRY_COUNT,
      staleTime: QUERY_STALE_TIME,
      refetchOnWindowFocus: false,
    },
  },
});

export function AppRoutes() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950 transition-colors duration-150">
      {/* Sidebar navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main workspace layout */}
      <div className="flex flex-col flex-1 h-full overflow-hidden">
        {/* Topbar navigation panel */}
        <Topbar onMenuToggle={() => setSidebarOpen(true)} />

        {/* Scrollable page view container */}
        <div className="flex-1 overflow-y-auto flex flex-col">
          <PageContainer>
            <Suspense fallback={<Loading />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/companies" element={<Companies />} />
                <Route path="/skills" element={<Skills />} />
                <Route path="/technology" element={<Technology />} />
                <Route path="/geography" element={<Geography />} />
                <Route path="/salary" element={<Salary />} />
                <Route path="/status" element={<Status />} />
                <Route path="/about" element={<About />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </PageContainer>
          <Footer />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ErrorBoundary>
          <AppRoutes />
        </ErrorBoundary>
      </BrowserRouter>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}
export { App };
