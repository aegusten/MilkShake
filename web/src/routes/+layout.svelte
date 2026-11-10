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
  });
</script>

{@render children()}
