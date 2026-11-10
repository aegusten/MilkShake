import { expect, test } from '@playwright/test';

const ADMIN = { email: process.env.ADMIN_EMAIL || 'admin@example.com', password: process.env.ADMIN_PASSWORD || 'ChangeMe123' };

test('a tap made before the scripts load is not lost', async ({ page }) => {
  // Hold every script until 3 seconds after the page starts, like a slow
  // phone connection. One shared gate, so dev mode's many modules don't
  // each add their own delay.
  const gate = Date.now() + 3000;
  await page.route('**/*', async (route) => {
    if (route.request().resourceType() === 'script') {
      await new Promise((r) => setTimeout(r, Math.max(0, gate - Date.now())));
    }
    await route.continue();
  });
  await page.goto('/?lang=en', { waitUntil: 'domcontentloaded' });
  expect(await page.evaluate(() => document.documentElement.dataset.hydrated)).toBeUndefined();

  await page.getByRole('button', { name: 'Add Cola to order' }).click();
  await page.getByRole('button', { name: 'Cocktails' }).click();

  await page.waitForFunction(() => document.documentElement.dataset.hydrated === 'true', null, { timeout: 30000 });
  await expect(page.locator('#order li [role=group]', { hasText: 'Cola' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cocktails' })).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('button[aria-busy="true"]')).toHaveCount(0);
});

test('keys 1, 2 and 3 jump between queue columns', async ({ page, request }) => {
  const { access_token } = await (await request.post('/api/admin/login', { data: ADMIN })).json();
  const drinks = await (await request.get('/api/drinks')).json();
  const auth = { Authorization: `Bearer ${access_token}` };
  const place = async (name) =>
    (await request.post('/api/orders', { data: { guest_name: name, items: [{ drink_id: drinks[0].id, quantity: 1 }] } })).json();
  const making = await place('Jump Making');
  await request.post(`/api/admin/orders/${making.id}/accept`, { headers: auth });
  const ready = await place('Jump Ready');
  await request.post(`/api/admin/orders/${ready.id}/accept`, { headers: auth });
  await request.post(`/api/admin/orders/${ready.id}/ready`, { headers: auth });
  await place('Jump New');

  await page.addInitScript((t) => localStorage.setItem('ms_admin_token', t), access_token);
  await page.goto('/admin/orders');
  await page.waitForFunction(() => document.documentElement.dataset.hydrated === 'true');
  await expect(page.locator('.skeleton')).toHaveCount(0);

  const focusedColumn = () => page.evaluate(() => document.activeElement?.closest('[data-status]')?.dataset.status);
  for (const [key, status] of [['3', 'ready'], ['1', 'pending'], ['2', 'accepted']]) {
    await page.keyboard.press(key);
    expect(await focusedColumn()).toBe(status);
    expect(await page.evaluate(() => document.activeElement?.hasAttribute('data-primary'))).toBe(true);
  }
});
