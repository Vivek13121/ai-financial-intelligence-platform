import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { LiveFeed } from "./pages/LiveFeed";
import { Analytics } from "./pages/Analytics";
import { Forecasts } from "./pages/Forecasts";
import { Search } from "./pages/Search";
import { Company } from "./pages/Company";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="feed" element={<LiveFeed />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="forecasts" element={<Forecasts />} />
            <Route path="search" element={<Search />} />
            <Route path="company/:name" element={<Company />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
