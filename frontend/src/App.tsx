import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SidebarLayout } from './components/layout/SidebarLayout';
import { DashboardPage } from './pages/DashboardPage';
import { LeafDiseasePage } from './pages/LeafDiseasePage';
import { PestDetectionPage } from './pages/PestDetectionPage';
import { UnifiedTestingPage } from './pages/UnifiedTestingPage';
import { LeafAdvisoryPage } from './pages/LeafAdvisoryPage';
import { CatalogPage } from './pages/CatalogPage';
import { HistoryPage } from './pages/HistoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <BrowserRouter>
      <SidebarLayout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/scan" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/leaf-disease/:runId?" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/pests" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/pest-detection" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/leaf-diagnosis" element={<UnifiedTestingPage />} />
          <Route path="/leaf-advisory" element={<LeafAdvisoryPage />} />
          <Route path="/test-lab" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/unified-test" element={<Navigate to="/leaf-diagnosis" replace />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SidebarLayout>
    </BrowserRouter>
  );
}

export default App;
