<script>
  import { LOCALES, LOCALE_LABEL } from '$lib/i18n.js';
  import { useLocale } from '$lib/locale.svelte.js';

  let { dark = false } = $props();
  const i18n = useLocale();

  // Links, not buttons, so switching works before the page's JavaScript has
  // loaded: the server sets the cookie and redirects back. Once hydrated,
  // the click is handled here instead and the switch is instant.
  function choose(event, code) {
    event.preventDefault();
    i18n.set(code);
  }
</script>

<nav aria-label={i18n.t('nav.language')} class="flex items-center gap-1">
  {#each LOCALES as code}
    <a
      href={`?lang=${code}`}
      hreflang={code}
      lang={code}
      aria-current={i18n.current === code ? 'true' : undefined}
      onclick={(event) => choose(event, code)}
      class={[
        'inline-flex min-h-11 min-w-11 items-center justify-center rounded-full px-3 text-xs font-bold transition',
        i18n.current === code
          ? dark
            ? 'bg-white text-ink'
            : 'bg-ink text-white'
          : dark
            ? 'text-tv-text hover:bg-white/10'
            : 'text-ink hover:bg-fog',
      ]}
    >
      {LOCALE_LABEL[code]}
    </a>
  {/each}
</nav>
