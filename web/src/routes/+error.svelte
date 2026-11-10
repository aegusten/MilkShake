<script>
  import { page } from '$app/state';
  import { useLocale } from '$lib/locale.svelte.js';

  const i18n = useLocale();
</script>

<svelte:head>
  <title>{i18n.t('error.title')} | MilkShake</title>
</svelte:head>

<main class="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-4 px-6 text-center">
  <p class="font-display text-7xl text-accent">{page.status}</p>
  <h1 class="text-2xl font-bold">
    {page.status === 404 ? i18n.t('error.notFound') : i18n.t('error.title')}
  </h1>
  {#if page.status !== 404 && page.error?.message}
    <p class="text-muted">{page.error.message}</p>
  {/if}
  <a class="btn-primary" href="/">{i18n.t('error.home')}</a>
</main>
