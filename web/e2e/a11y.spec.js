// Accessibility scan of every screen with axe-core (WCAG 2.1 A and AA).
// Run against a live stack: BASE_URL=http://localhost:5173 npx playwright test
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'admin@example.com';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'ChangeMe123';

async function scan(page) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  const summary = results.violations.map(
    (v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(' ')).slice(0, 3).join(' | ')}`
  );
  expect(summary).toEqual([]);
}

for (const [name, path] of [
  ['menu', '/'],
  ['pickup tv', '/display'],
  ['qr', '/qr'],
  ['not found', '/no-such-page'],
]) {
  test(`${name} has no WCAG A/AA violations`, async ({ page }) => {
    await page.goto(path);
    await scan(page);
  });
}

test('menu in russian has no violations', async ({ page, context, baseURL }) => {
  await context.addCookies([{ name: 'ms_lang', value: 'ru', url: baseURL }]);
  await page.goto('/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
  await scan(page);
});

test('language switch survives a reload', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'RUS' }).click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('lang', 'ru');
  await page.getByRole('link', { name: 'ENG' }).click();
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByRole('heading', { level: 1 })).toHaveText('Pick a drink. Add to order. Done.');
});

test.describe('without javascript', () => {
  test.use({ javaScriptEnabled: false });

  test('the menu renders and the language can still be switched', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 3 }).first()).toBeVisible();
    await page.getByRole('link', { name: 'RUS' }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Выберите напиток. Добавьте. Готово.');
  });
});

test('menu with a filled cart has no violations', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /^Add .* to order$/ }).first().click();
  await page.getByRole('button', { name: /^Add .* to order$/ }).nth(1).click();
  await scan(page);
});

test('staff sign-in has no violations', async ({ page }) => {
  await page.goto('/admin');
  await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  await scan(page);
});

for (const path of ['/admin/orders', '/admin/drinks']) {
  test(`staff ${path} has no violations`, async ({ page, request }) => {
    const login = await request.post('/api/admin/login', {
      data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
    });
    const { access_token } = await login.json();
    await page.addInitScript((token) => localStorage.setItem('ms_admin_token', token), access_token);
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    // Let skeletons resolve so the real content is what gets scanned. Not
    // networkidle: the live stream keeps the network busy forever.
    await expect(page.locator('.skeleton')).toHaveCount(0);
    await scan(page);
  });
}

test('staff queue works with the keyboard alone', async ({ page, request }) => {
  const login = await request.post('/api/admin/login', {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  const { access_token } = await login.json();
  const drinks = await (await request.get('/api/drinks')).json();
  const placed = await (
    await request.post('/api/orders', {
      data: { guest_name: 'Keyboard', items: [{ drink_id: drinks[0].id, quantity: 1 }] },
    })
  ).json();

  await page.addInitScript((token) => localStorage.setItem('ms_admin_token', token), access_token);
  await page.goto('/admin/orders');
  const accept = page.getByRole('button', { name: `Accept, ticket ${placed.ticket}` });
  await expect(accept).toBeVisible();

  // Tab until the accept button for this ticket has focus, then use Enter only.
  for (let i = 0; i < 400 && !(await accept.evaluate((el) => el === document.activeElement)); i++) {
    await page.keyboard.press('Tab');
  }
  await expect(accept).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: `Mark ready, ticket ${placed.ticket}` })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: `Picked up, ticket ${placed.ticket}` })).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: `Picked up, ticket ${placed.ticket}` })).toHaveCount(0);
});
