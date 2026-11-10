<script>
  import { useLocale } from '$lib/locale.svelte.js';

  let { item, onchange, onremove } = $props();
  const i18n = useLocale();

  // Swipe left to remove. Pointer events cover touch and mouse; past a third
  // of the row it commits, short of that it snaps back. The minus button
  // and the remove button do the same job for anyone not swiping.
  const COMMIT_RATIO = 0.33;
  let row;
  let startX = $state(null);
  let dx = $state(0);
  let leaving = $state(false);

  function down(e) {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    startX = e.clientX;
  }
  function move(e) {
    if (startX === null) return;
    dx = Math.min(0, e.clientX - startX);
  }
  function up() {
    if (startX === null) return;
    startX = null;
    if (-dx > row.offsetWidth * COMMIT_RATIO) {
      leaving = true;
      dx = -row.offsetWidth;
      setTimeout(() => onremove(item.id), 180);
    } else {
      dx = 0;
    }
  }
</script>

<li class="relative overflow-hidden rounded-xl">
  <div class="absolute inset-0 flex items-center justify-end bg-accent-strong pr-6 text-white" aria-hidden="true">
    <svg viewBox="0 0 24 24" class="size-6"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13" /></svg>
  </div>
  <div
    bind:this={row}
    class="relative flex touch-pan-y items-center gap-3 bg-card px-1 py-3"
    style:transform={`translateX(${dx}px)`}
    style:transition={startX === null ? 'transform 180ms ease-out' : 'none'}
    style:opacity={leaving ? 0 : 1}
    onpointerdown={down}
    onpointermove={move}
    onpointerup={up}
    onpointercancel={up}
    role="group"
    aria-label={item.name}
  >
    <div class="min-w-0 flex-1">
      <p class="truncate font-semibold">{item.name}</p>
      <p class="text-sm text-muted">{i18n.price(item.price)}</p>
    </div>
    <div class="flex items-center gap-1">
      <button
        type="button"
        class="btn-ghost size-11 px-0"
        aria-label={i18n.t('cart.decrease', { name: item.name })}
        onclick={() => onchange(item.id, -1)}
      >−</button>
      <span class="w-6 text-center font-semibold" aria-live="polite">{item.qty}</span>
      <button
        type="button"
        class="btn-ghost size-11 px-0"
        aria-label={i18n.t('cart.increase', { name: item.name })}
        onclick={() => onchange(item.id, 1)}
      >+</button>
    </div>
    <span class="w-28 text-right text-sm font-semibold">{i18n.price(item.price * item.qty)}</span>
    <button
      type="button"
      class="btn-danger size-11 px-0"
      aria-label={i18n.t('cart.remove', { name: item.name })}
      onclick={() => onremove(item.id)}
    >
      <svg viewBox="0 0 20 20" class="size-4" aria-hidden="true"><path fill="currentColor" d="M6 6l8 8M14 6l-8 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    </button>
  </div>
</li>
