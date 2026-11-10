<script>
  import { onDestroy, onMount, tick } from 'svelte';
  import { api, liveEvents, storage } from '$lib/api.js';
  import { useLocale } from '$lib/locale.svelte.js';
  import CartRow from '$lib/components/CartRow.svelte';
  import DrinkCard from '$lib/components/DrinkCard.svelte';
  import LangSwitch from '$lib/components/LangSwitch.svelte';
  import TicketCard from '$lib/components/TicketCard.svelte';

  let { data } = $props();
  const i18n = useLocale();

  const FINISHED = ['completed', 'cancelled'];
  const LAST_ORDER_KEY = 'ms_last_order';

  let query = $state('');
  let category = $state('all');
  let cart = $state([]);
  let guestName = $state('');
  let guestPhone = $state('');
  let formError = $state('');
  let sending = $state(false);
  let myOrder = $state(null);
  let stopFollowing = null;

  const count = $derived(cart.reduce((n, item) => n + item.qty, 0));
  const total = $derived(cart.reduce((sum, item) => sum + item.price * item.qty, 0));
  const featured = $derived(data.drinks[0]);
  const visible = $derived(
    data.drinks.filter((drink) => {
      const text = `${drink.name} ${drink.description ?? ''}`.toLowerCase();
      const matches = text.includes(query.trim().toLowerCase());
      const inCategory =
        category === 'all' || (drink.item_masters ?? []).some((m) => m.id === category);
      return matches && inCategory;
    })
  );

  function add(drink) {
    const existing = cart.find((item) => item.id === drink.id);
    if (existing) existing.qty += 1;
    else cart.push({ id: drink.id, name: drink.name, price: drink.price, qty: 1 });
    formError = '';
  }

  function change(id, delta) {
    const item = cart.find((entry) => entry.id === id);
    if (!item) return;
    item.qty += delta;
    if (item.qty <= 0) remove(id);
  }

  function remove(id) {
    cart = cart.filter((item) => item.id !== id);
  }

  // --- The guest's own order, followed live until it is picked up. -------

  function unfollow() {
    stopFollowing?.();
    stopFollowing = null;
  }

  async function follow(order, { scroll = false } = {}) {
    myOrder = order;
    unfollow();
    if (FINISHED.includes(order.status)) {
      storage.set(LAST_ORDER_KEY, null);
      return;
    }
    storage.set(LAST_ORDER_KEY, order.id);
    stopFollowing = liveEvents(`/api/stream/orders/${order.id}`, {
      order: ({ order: updated }) => {
        myOrder = updated;
        if (FINISHED.includes(updated.status)) {
          unfollow();
          storage.set(LAST_ORDER_KEY, null);
        }
      },
    });
    if (scroll) {
      await tick();
      document.getElementById('ticket')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function newOrder() {
    unfollow();
    myOrder = null;
  }

  async function placeOrder(event) {
    event.preventDefault();
    formError = '';
    if (!guestName.trim()) {
      formError = i18n.t('cart.nameRequired');
      document.getElementById('guest-name')?.focus();
      return;
    }
    sending = true;
    const response = await api.placeOrder({
      guest_name: guestName.trim(),
      phone: guestPhone.trim() || null,
      items: cart.map((item) => ({ drink_id: item.id, quantity: item.qty })),
    });
    sending = false;
    if (!response.ok) {
      formError = response.data?.detail || i18n.t('cart.failed');
      return;
    }
    cart = [];
    guestName = '';
    guestPhone = '';
    follow(response.data, { scroll: true });
  }

  onMount(async () => {
    const id = storage.get(LAST_ORDER_KEY);
    if (!id) return;
    const response = await api.guestOrder(id);
    if (response.ok && !FINISHED.includes(response.data.status)) follow(response.data);
    else storage.set(LAST_ORDER_KEY, null);
  });

  onDestroy(unfollow);
</script>

<svelte:head>
  <title>{i18n.t('meta.title')}</title>
  <meta name="description" content={i18n.t('meta.description')} />
</svelte:head>

<a
  href="#menu"
  class="sr-only z-50 rounded-full bg-ink px-4 py-2 text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
>
  {i18n.t('nav.skip')}
</a>

<header class="sticky top-0 z-30 border-b border-line bg-canvas/90 backdrop-blur">
  <div class="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
    <a href="/" class="mr-auto flex items-center gap-3">
      <span class="size-9 rounded-xl bg-accent" aria-hidden="true"></span>
      <span class="flex flex-col leading-none">
        <span class="font-display text-2xl tracking-wide">MilkShake</span>
        <span class="text-xs text-muted">{i18n.t('nav.brandTag')}</span>
      </span>
    </a>
    <LangSwitch />
    <label class="w-full sm:w-64">
      <span class="sr-only">{i18n.t('search.placeholder')}</span>
      <input
        type="search"
        class="field py-2.5"
        placeholder={i18n.t('search.placeholder')}
        bind:value={query}
      />
    </label>
  </div>
</header>

<main class="mx-auto flex max-w-6xl flex-col gap-12 px-4 pt-8 pb-32">
  <section class="grid items-center gap-6 md:grid-cols-[1.3fr_1fr]">
    <div>
      <p class="text-xs font-bold uppercase tracking-widest text-accent-strong">{i18n.t('hero.eyebrow')}</p>
      <h1 class="mt-2 font-display text-6xl leading-[0.95] sm:text-7xl">{i18n.t('hero.title')}</h1>
      <p class="mt-4 max-w-md text-muted">{i18n.t('hero.body')}</p>
    </div>
    {#if featured}
      <div class="card flex flex-col gap-3 p-6">
        <div class="flex items-center justify-between">
          <span class="rounded-full bg-ink px-3 py-1 text-xs font-bold text-white">{i18n.t('hero.featured')}</span>
          <span class="font-semibold">{i18n.price(featured.price)}</span>
        </div>
        <p class="text-2xl font-bold">{featured.name}</p>
        {#if featured.description}<p class="text-muted">{featured.description}</p>{/if}
        <button type="button" class="btn-accent self-start" onclick={() => add(featured)}>
          {i18n.t('menu.add')}
        </button>
      </div>
    {/if}
  </section>

  <section id="menu" aria-labelledby="menu-title" class="scroll-mt-28">
    <div class="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 id="menu-title" class="font-display text-5xl">{i18n.t('menu.title')}</h2>
        <p class="text-muted">{i18n.t('menu.body')}</p>
      </div>
      {#if data.itemMasters.length}
        <div role="group" aria-label={i18n.t('menu.title')} class="flex flex-wrap gap-2">
          {#each [{ id: 'all', name: i18n.t('menu.all') }, ...data.itemMasters] as m (m.id)}
            <button
              type="button"
              aria-pressed={category === m.id}
              onclick={() => (category = m.id)}
              class={[
                'btn min-h-10 border',
                category === m.id ? 'border-ink bg-ink text-white' : 'border-line bg-card text-ink hover:bg-fog',
              ]}
            >
              {m.name}
            </button>
          {/each}
        </div>
      {/if}
    </div>

    {#if data.loadFailed}
      <p class="card p-6 text-muted" role="alert">{i18n.t('menu.loadFailed')}</p>
    {:else if data.drinks.length === 0}
      <p class="card p-6 text-muted">{i18n.t('menu.empty')}</p>
    {:else if visible.length === 0}
      <div class="card p-6">
        <p class="font-semibold">{i18n.t('menu.noResultsTitle')}</p>
        <p class="text-muted">{i18n.t('menu.noResultsBody')}</p>
      </div>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {#each visible as drink, index (drink.id)}
          <DrinkCard {drink} onadd={add} eager={index < 3} />
        {/each}
      </div>
    {/if}
  </section>

  <section id="order" aria-labelledby="order-title" class="scroll-mt-28">
    <h2 id="order-title" class="mb-4 font-display text-5xl">{i18n.t('cart.title')}</h2>

    {#if myOrder}
      <div id="ticket" class="mb-6">
        <TicketCard order={myOrder} finished={FINISHED.includes(myOrder.status)} onnew={newOrder} />
      </div>
    {/if}

    <form class="card flex flex-col gap-5 p-5 sm:p-6" onsubmit={placeOrder} novalidate>
      {#if cart.length === 0}
        <p class="text-muted">{i18n.t('cart.empty')}</p>
      {:else}
        <ul class="flex flex-col divide-y divide-line" aria-label={i18n.t('cart.items', { count })}>
          {#each cart as item (item.id)}
            <CartRow {item} onchange={change} onremove={remove} />
          {/each}
        </ul>
        <p class="text-xs text-muted">{i18n.t('cart.swipeHint')}</p>
        <div class="flex items-center justify-between border-t border-line pt-4 text-lg font-bold">
          <span>{i18n.t('cart.total')} · {i18n.t('cart.items', { count })}</span>
          <span>{i18n.price(total)}</span>
        </div>
      {/if}

      <div class="grid gap-4 sm:grid-cols-2">
        <label class="label" for="guest-name">
          {i18n.t('cart.name')}
          <input
            id="guest-name"
            class="field"
            autocomplete="given-name"
            placeholder={i18n.t('cart.namePlaceholder')}
            aria-invalid={formError === i18n.t('cart.nameRequired')}
            aria-describedby={formError ? 'form-error' : undefined}
            bind:value={guestName}
          />
        </label>
        <label class="label" for="guest-phone">
          {i18n.t('cart.phone')}
          <input
            id="guest-phone"
            class="field"
            type="tel"
            autocomplete="tel"
            placeholder={i18n.t('cart.phonePlaceholder')}
            bind:value={guestPhone}
          />
        </label>
      </div>

      {#if formError}
        <p id="form-error" class="font-semibold text-accent-strong" role="alert">{formError}</p>
      {/if}

      <button type="submit" class="btn-accent w-full sm:w-auto sm:self-end" disabled={sending || cart.length === 0}>
        {sending ? i18n.t('cart.sending') : i18n.t('cart.place')}
      </button>
    </form>
  </section>

  <footer class="border-t border-line pt-6 text-sm text-muted">
    <p>{i18n.t('footer.about')}</p>
  </footer>
</main>

{#if count > 0}
  <!-- Phones: the order form is below the whole menu, so keep a way to it in reach. -->
  <a
    href="#order"
    class="fixed inset-x-4 bottom-4 z-40 flex items-center justify-between rounded-full bg-ink px-6 py-4 text-white shadow-card md:hidden"
  >
    <span class="font-semibold">{i18n.t('cart.items', { count })}</span>
    <span class="font-bold">{i18n.price(total)}</span>
  </a>
{/if}
