// Every language must carry every key, with the same {placeholders}.
// Runs in Node, no browser needed.
import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';

const load = (lang) => JSON.parse(readFileSync(new URL(`../messages/${lang}.json`, import.meta.url), 'utf8'));
const placeholders = (value) =>
  [...JSON.stringify(value).matchAll(/\{(\w+)\}/g)].map((m) => m[1]).filter((v, i, a) => a.indexOf(v) === i).sort().join(',');

const en = load('en');

for (const lang of ['ru', 'uz']) {
  test(`${lang} has every english key with the same placeholders`, () => {
    const other = load(lang);
    expect(Object.keys(other).sort()).toEqual(Object.keys(en).sort());
    for (const key of Object.keys(en)) {
      expect(placeholders(other[key]), `${lang}:${key}`).toBe(placeholders(en[key]));
    }
  });
}

test('plural messages always have an "other" form', () => {
  for (const lang of ['en', 'ru', 'uz']) {
    for (const [key, value] of Object.entries(load(lang))) {
      if (typeof value === 'object') expect(value.other, `${lang}:${key}`).toBeDefined();
    }
  }
});
