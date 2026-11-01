import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { AuthProvider, ProtectedRoute } from './auth';
import { Layout } from './components';
import AuthPage from './pages/AuthPage';
import CatalogPage from './pages/CatalogPage';
import MovieDetailPage from './pages/MovieDetailPage';
import MovieFormPage from './pages/MovieFormPage';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><BrowserRouter><AuthProvider><Layout><Routes>
    <Route path="/" element={<CatalogPage />} />
    <Route path="/login" element={<AuthPage key="login" />} />
    <Route path="/register" element={<AuthPage key="register" register />} />
    <Route path="/favorites" element={<ProtectedRoute><CatalogPage favorites /></ProtectedRoute>} />
    <Route path="/items/new" element={<ProtectedRoute admin><MovieFormPage /></ProtectedRoute>} />
    <Route path="/items/:id" element={<MovieDetailPage />} />
    <Route path="/items/:id/edit" element={<ProtectedRoute admin><MovieFormPage /></ProtectedRoute>} />
    <Route path="*" element={<div className="empty"><h1>Страница не найдена</h1><Link to="/">Вернуться в каталог</Link></div>} />
  </Routes></Layout></AuthProvider></BrowserRouter></React.StrictMode>,
);
