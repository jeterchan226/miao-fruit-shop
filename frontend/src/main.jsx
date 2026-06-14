import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import '../assets/site.css';
import '../assets/admin.css';
import '../assets/tw-zipcode.js';
import AdminApp from './AdminApp.jsx';
import StorefrontApp from './App.jsx';

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<StorefrontApp />} />
        <Route path="/admin" element={<AdminApp />} />
        <Route path="/admin.html" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
