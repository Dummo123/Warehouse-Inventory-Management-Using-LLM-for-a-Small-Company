import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import dayjs from "dayjs";
import "dayjs/locale/ru";

import AppLayout from "./components/layout/AppLayout";
import LoginPage from "./pages/LoginPage";
import StockPage from "./pages/StockPage";
import MovementsPage from "./pages/MovementsPage";
import ArticlesPage from "./pages/ArticlesPage";
import PurchasesPage from "./pages/PurchasesPage";
import ProductionPage from "./pages/ProductionPage";
import ShipmentsPage from "./pages/ShipmentsPage";
import ReturnsPage from "./pages/ReturnsPage";
import FinancePage from "./pages/FinancePage";
import UsersPage from "./pages/UsersPage";
import ReportsPage from "./pages/ReportsPage";
import AssistantPage from "./pages/AssistantPage";

dayjs.locale("ru");

function RequireAuth({ children }: { children: JSX.Element }) {
  if (!localStorage.getItem("token")) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <ConfigProvider locale={ruRU} theme={{ token: { borderRadius: 6 } }}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<RequireAuth><AppLayout /></RequireAuth>}>
            <Route index element={<Navigate to="/stock" replace />} />
            <Route path="stock"      element={<StockPage />} />
            <Route path="movements"  element={<MovementsPage />} />
            <Route path="articles"   element={<ArticlesPage />} />
            <Route path="purchases"  element={<PurchasesPage />} />
            <Route path="production" element={<ProductionPage />} />
            <Route path="shipments"  element={<ShipmentsPage />} />
            <Route path="returns"    element={<ReturnsPage />} />
            <Route path="finance"    element={<FinancePage />} />
            <Route path="users"      element={<UsersPage />} />
            <Route path="reports"    element={<ReportsPage />} />
            <Route path="assistant"  element={<AssistantPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
