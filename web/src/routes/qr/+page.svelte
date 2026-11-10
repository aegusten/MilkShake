<script>
  import { useLocale } from '$lib/locale.svelte.js';
  import LangSwitch from '$lib/components/LangSwitch.svelte';

  let { data } = $props();
  const i18n = useLocale();
</script>

<svelte:head>
  <title>{i18n.t('qr.title')} | MilkShake</title>
</svelte:head>

<main class="flex min-h-screen flex-col items-center justify-center gap-8 px-6 py-10 text-center">
  <div class="absolute top-4 right-4"><LangSwitch /></div>
  <div>
    <p class="font-display text-3xl text-accent-strong">MilkShake</p>
    <h1 class="font-display text-6xl sm:text-7xl">{i18n.t('qr.title')}</h1>
    <p class="mt-2 text-muted">{i18n.t('qr.body')}</p>
  </div>
  <figure class="card w-full max-w-sm p-6">
    <div class="[&>svg]:h-auto [&>svg]:w-full" role="img" aria-label={`QR code: ${data.target}`}>
      {@html data.svg}
    </div>
    <figcaption class="mt-4 break-all text-sm font-semibold">{data.target}</figcaption>
  </figure>
  {#if data.isLocal}
    <p class="max-w-md text-sm text-muted">
      This page was opened on localhost, which a phone can't reach. Open it via the computer's LAN
      address, or set PUBLIC_MENU_URL.
    </p>
  {/if}
</main>
