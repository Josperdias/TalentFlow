import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// base './' + HashRouter: o pacote funciona na raiz do domínio ou em subpasta, em qualquer servidor estático,
// sem regras de reescrita. A URL da API vem de config.json (editável sem recompilar).
export default defineConfig({
  base: './',
  plugins: [react()],
  build: { target: 'es2020', sourcemap: false, assetsInlineLimit: 0 },
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  test: { environment: 'jsdom', globals: true }
});
