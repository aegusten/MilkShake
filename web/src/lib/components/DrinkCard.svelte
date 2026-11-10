<script>
  import { useLocale } from '$lib/locale.svelte.js';

  let { drink, onadd, eager = false } = $props();
  const i18n = useLocale();
</script>

<article class="card flex flex-col overflow-hidden">
  {#if drink.image_cover}
    <img
      src={drink.image_cover}
      alt=""
      width="640"
      height="400"
      loading={eager ? 'eager' : 'lazy'}
      decoding="async"
      class="aspect-[16/10] w-full object-cover"
    />
  {:else}
    <div class="flex aspect-[16/10] w-full items-center justify-center bg-fog" aria-hidden="true">
      <span class="font-display text-5xl text-line">{drink.name.slice(0, 1)}</span>
    </div>
  {/if}
  <div class="flex flex-1 flex-col gap-2 p-4">
    <div class="flex items-start justify-between gap-3">
      <h3 class="text-lg font-bold leading-tight">{drink.name}</h3>
      <span class="shrink-0 text-sm font-semibold">{i18n.price(drink.price)}</span>
    </div>
    {#if drink.description}
      <p class="text-sm text-muted">{drink.description}</p>
    {/if}
    <button
      type="button"
      class="btn-ghost mt-auto w-full"
      aria-label={i18n.t('menu.addNamed', { name: drink.name })}
      onclick={() => onadd(drink)}
    >
      {i18n.t('menu.add')}
    </button>
  </div>
</article>
