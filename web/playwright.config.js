import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'e2e',
  timeout: 30000,
  // One worker: these tests share one live order queue, and a test placing an
  // order would shift the staff screen while another test is scanning it.
  workers: 1,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    // Cards fade in from transparent. Without this, axe sometimes measures
    // contrast mid-fade and reports text that is fine once it settles.
    reducedMotion: 'reduce',
  },
  reporter: 'list',
});
