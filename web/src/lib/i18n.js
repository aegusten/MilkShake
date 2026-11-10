// Small i18n layer: messages live in /messages/{lang}.json.
//
// Not svelte-i18n: that library keeps the locale in a module-level store,
// which on the server is shared by every concurrent request, so two guests
// could get each other's language. Here the locale comes from a cookie in
// the request, travels down through page data, and translation is a pure
// function of (locale, key).

import en from '../../messages/en.json';
import ru from '../../messages/ru.json';
import uz from '../../messages/uz.json';

export const LOCALES = ['en', 'ru', 'uz'];
export const DEFAULT_LOCALE = 'en';
export const LOCALE_COOKIE = 'ms_lang';

const MESSAGES = { en, ru, uz };

// BCP 47 tags for Intl. Uzbek in Latin script, which is what the copy uses.
const INTL_TAG = { en: 'en-US', ru: 'ru-RU', uz: 'uz-Latn-UZ' };

export const LOCALE_LABEL = { en: 'ENG', ru: 'RUS', uz: 'UZB' };

export function resolveLocale(value) {
  return LOCALES.includes(value) ? value : DEFAULT_LOCALE;
}

function interpolate(text, params) {
  return text.replace(/\{(\w+)\}/g, (_, name) => (name in params ? String(params[name]) : `{${name}}`));
}

/**
 * Translate ``key``. A message that is an object is a plural: the form is
 * picked by Intl.PluralRules from ``params.count``, so Russian gets its
 * one/few/many forms right. Falls back to English, then to the key itself.
 */
export function translate(locale, key, params = {}) {
  const message = MESSAGES[locale]?.[key] ?? MESSAGES[DEFAULT_LOCALE][key];
  if (message === undefined) return key;
  if (typeof message === 'object') {
    const form = new Intl.PluralRules(INTL_TAG[locale]).select(params.count ?? 0);
    return interpolate(message[form] ?? message.other, params);
  }
  return interpolate(message, params);
}

export function formatPrice(locale, value) {
  if (locale === 'uz') {
    // Built by hand: browsers ship patchy Uzbek data. Chrome 157 claims to
    // support uz-Latn-UZ yet formats "UZS 8,000", while Node gives
    // "8 000 soʻm", so the server and the browser disagreed and the page
    // switched format as it loaded. Grouping matches the Uzbek convention.
    const digits = Math.round(Number(value)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return `${digits} soʻm`;
  }
  return new Intl.NumberFormat(INTL_TAG[locale], {
    style: 'currency',
    currency: 'UZS',
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatTime(locale, value) {
  if (!value) return '';
  return new Intl.DateTimeFormat(INTL_TAG[locale], { hour: '2-digit', minute: '2-digit' }).format(
    new Date(value)
  );
}

/** Every key in English must exist in every other language. */
export function missingKeys() {
  const missing = [];
  for (const locale of LOCALES) {
    for (const key of Object.keys(en)) {
      if (!(key in MESSAGES[locale])) missing.push(`${locale}:${key}`);
    }
  }
  return missing;
}
