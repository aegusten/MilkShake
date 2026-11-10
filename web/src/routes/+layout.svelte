<script>
  import '../app.css';
  import { provideLocale } from '$lib/locale.svelte.js';

  let { data, children } = $props();

  // Initial value only; after this the client owns the locale.
  // svelte-ignore state_referenced_locally
  provideLocale(data.locale);
</script>

{@render children()}
