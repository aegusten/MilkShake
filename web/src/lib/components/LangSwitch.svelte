<script>
  import { LOCALES, LOCALE_LABEL } from '$lib/i18n.js';
  import { useLocale } from '$lib/locale.svelte.js';

  let { dark = false } = $props();
  const i18n = useLocale();
</script>

<div role="group" aria-label={i18n.t('nav.language')} class="flex items-center gap-1">
  {#each LOCALES as code}
    <button
      type="button"
      lang={code}
      aria-pressed={i18n.current === code}
      onclick={() => i18n.set(code)}
      class={[
        'min-h-11 min-w-11 rounded-full px-3 text-xs font-bold transition',
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
    </button>
  {/each}
</div>
