import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import './styles/app.css';
import { loadConfig } from './config';
import { AuthProvider } from './state';
import App from './App';

loadConfig().finally(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode><HashRouter><AuthProvider><App /></AuthProvider></HashRouter></StrictMode>
  );
});
