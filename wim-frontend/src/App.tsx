import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import ruRU from "antd/locale/ru_RU";
import dayjs from "dayjs";
import "dayjs/locale/ru";

import AppLayout from "./components/layout/AppLayout";
import StockPage from "./pages/StockPage";
import MovementsPage from "./pages/MovementsPage";
import ArticlesPage from "./pages/ArticlesPage";
import PurchasesPage from "./pages/PurchasesPage";
import PurchaseFormPage from "./pages/PurchaseFormPage";
import ProductionPage from "./pages/ProductionPage";
import ProductionFormPage from "./pages/ProductionFormPage";
import ShipmentsPage from "./pages/ShipmentsPage";
import ShipmentFormPage from "./pages/ShipmentFormPage";
import ReturnsPage from "./pages/ReturnsPage";
import ReturnFormPage from "./pages/ReturnFormPage";
import FinancePage from "./pages/FinancePage";
import UsersPage from "./pages/UsersPage";
import ReportsPage from "./pages/ReportsPage";
import AssistantPage from "./pages/AssistantPage";

dayjs.locale("ru");

export default function App() {
  return (
    <ConfigProvider locale={ruRU} theme={{ token: { borderRadius: 6 } }}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Navigate to="/stock" replace />} />
            <Route path="stock" element={<StockPage />} />
            <Route path="movements" element={<MovementsPage />} />
            <Route path="articles" element={<ArticlesPage />} />
            <Route path="purchases" element={<PurchasesPage />} />
            <Route path="purchases/new" element={<PurchaseFormPage />} />
            <Route path="production" element={<ProductionPage />} />
            <Route path="production/new" element={<ProductionFormPage />} />
            <Route path="shipments" element={<ShipmentsPage />} />
            <Route path="shipments/new" element={<ShipmentFormPage />} />
            <Route path="returns" element={<ReturnsPage />} />
            <Route path="returns/new" element={<ReturnFormPage />} />
            <Route path="finance" element={<FinancePage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="assistant" element={<AssistantPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}