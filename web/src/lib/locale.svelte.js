import { getContext, setContext } from 'svelte';
import {
  LOCALE_COOKIE,
  formatPrice,
  formatTime,
  resolveLocale,
  translate,
} from './i18n.js';
import { storage } from './api.js';

const KEY = Symbol('locale');
const ONE_YEAR = 60 * 60 * 24 * 365;

class Locale {
  current = $state('en');

  constructor(initial) {
    this.current = resolveLocale(initial);
  }

  t = (key, params) => translate(this.current, key, params);
  price = (value) => formatPrice(this.current, value);
  time = (value) => formatTime(this.current, value);

  /** Switch language. The cookie lets the server render the next visit in
   *  this language with no flash; localStorage is kept as a mirror. */
  set = (value) => {
    this.current = resolveLocale(value);
    document.cookie = `${LOCALE_COOKIE}=${this.current}; path=/; max-age=${ONE_YEAR}; samesite=lax`;
    storage.set(LOCALE_COOKIE, this.current);
    document.documentElement.lang = this.current;
  };
}

export function provideLocale(initial) {
  return setContext(KEY, new Locale(initial));
}

export function useLocale() {
  return getContext(KEY);
}
