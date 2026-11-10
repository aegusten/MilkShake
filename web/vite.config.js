import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  server: {
    host: true,
    port: 5173,
    // Extra hostnames the dev server answers to, e.g. "frontend" so the
    // Playwright container can reach it over the compose network.
    allowedHosts: process.env.VITE_ALLOWED_HOSTS ? process.env.VITE_ALLOWED_HOSTS.split(',') : [],
    // Docker bind mounts on Windows and macOS do not deliver file-change
    // events, so the dev server would keep serving stale modules.
    watch: process.env.VITE_USE_POLLING === 'true' ? { usePolling: true, interval: 300 } : undefined,
  },
});
