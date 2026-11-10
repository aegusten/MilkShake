<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { provideLocale } from '$lib/locale.svelte.js';

  let { data, children } = $props();

  // Initial value only; after this the client owns the locale.
  // svelte-ignore state_referenced_locally
  provideLocale(data.locale);

  // Marks the moment buttons start working. Before this the server-rendered
  // page is visible but only links respond; tests wait on it.
  onMount(() => {
    document.documentElement.dataset.hydrated = 'true';
    // Replay taps made before the app was live (recorded in app.html).
    // Child components mount before this layout, so their handlers exist.
    const pending = window.__msPending ?? [];
    window.__msPending = [];
    for (const key of pending) {
      const button = document.querySelector(`button[data-replay="${CSS.escape(key)}"]`);
      button?.removeAttribute('aria-busy');
      button?.click();
    }
    document.querySelectorAll('button[aria-busy="true"]').forEach((b) => b.removeAttribute('aria-busy'));
  });
</script>

{@render children()}
