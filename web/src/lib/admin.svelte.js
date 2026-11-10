import { getContext, setContext } from 'svelte';
import { api } from './api.js';

const KEY = Symbol('admin');

class AdminSession {
  loggedIn = $state(false);
  notice = $state('');

  constructor() {
    this.loggedIn = api.isLoggedIn();
  }

  expired = (message = 'Your session ended. Please sign in again.') => {
    api.logout();
    this.loggedIn = false;
    this.notice = message;
  };

  logout = () => {
    api.logout();
    this.loggedIn = false;
    this.notice = '';
  };
}

export const provideAdmin = () => setContext(KEY, new AdminSession());
export const useAdmin = () => getContext(KEY);
