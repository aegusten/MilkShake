<script>
  import { onDestroy, onMount, tick } from 'svelte';
  import { api, streamAdminOrders } from '$lib/api.js';
  import { useAdmin } from '$lib/admin.svelte.js';
  import { formatPrice, formatTime } from '$lib/i18n.js';

  const session = useAdmin();

  const OPEN = ['pending', 'accepted', 'ready'];
  const COLUMNS = [
    { status: 'pending', title: 'New' },
    { status: 'accepted', title: 'Making' },
    { status: 'ready', title: 'Ready for pickup' },
  ];
  // The forward button each status offers. Cancel is offered on all of them.
  const NEXT = {
    pending: { action: 'accept', label: 'Accept' },
    accepted: { action: 'ready', label: 'Mark ready' },
    ready: { action: 'complete', label: 'Picked up' },
  };
  const STREAM_LABEL = { live: 'Live', reconnecting: 'Reconnecting...', connecting: 'Connecting...' };

  let orders = $state([]);
  let loaded = $state(false);
  let error = $state('');
  let streamStatus = $state('connecting');
  let busy = $state(new Set());
  let announcement = $state('');
  let stop = null;

  const byStatus = $derived(
    Object.fromEntries(COLUMNS.map(({ status }) => [status, orders.filter((o) => o.status === status)]))
  );

  // Replace by id, drop orders that left the open states, oldest first so
  // the next ticket to make is at the top.
  function upsert(order) {
    const rest = orders.filter((o) => o.id !== order.id);
    orders = (OPEN.includes(order.status) ? [...rest, order] : rest).sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at)
    );
  }

  async function act(order, action) {
    error = '';
    busy = new Set([...busy, order.id]);
    const response = await api.changeOrderStatus(order.id, action);
    busy.delete(order.id);
    busy = new Set(busy);
    if (response.status === 401) return session.expired();
    if (!response.ok) {
      error = response.data?.detail || 'Could not update the order.';
      return;
    }
    upsert(response.data);
    announcement = `Ticket ${response.data.ticket} ${response.data.status}`;
    // The card just moved to another column and took keyboard focus with
    // it into the void. Put focus back on the same ticket's next button, or
    // on the queue if the ticket is done.
    await tick();
    const next = document.querySelector(`[data-order="${order.id}"] [data-primary]`);
    (next ?? document.getElementById('queue'))?.focus();
  }

  onMount(() => {
    stop = streamAdminOrders({
      onEvent: ({ event, data }) => {
        if (event === 'snapshot') {
          orders = [];
          data.orders.forEach(upsert);
          loaded = true;
        } else if (event === 'order') {
          const isNew = !orders.some((o) => o.id === data.order.id);
          upsert(data.order);
          if (isNew && data.order.status === 'pending') announcement = `New order, ticket ${data.order.ticket}`;
        }
      },
      onStatus: (status) => (streamStatus = status),
      onUnauthorized: () => session.expired(),
    });
  });
  onDestroy(() => stop?.());
</script>

<div class="mb-5 flex flex-wrap items-center gap-3">
  <h1 class="font-display text-5xl">Order queue</h1>
  <p class="ml-auto flex items-center gap-2 text-sm font-semibold" data-testid="stream-status">
    <span
      class={['size-2.5 rounded-full', streamStatus === 'live' ? 'bg-ok' : streamStatus === 'reconnecting' ? 'bg-warn' : 'bg-line']}
      aria-hidden="true"
    ></span>
    {STREAM_LABEL[streamStatus]}
  </p>
</div>

<p class="sr-only" role="status" aria-live="polite">{announcement}</p>

{#if error}
  <p class="card mb-4 p-4 font-semibold text-accent-strong" role="alert">{error}</p>
{/if}

<div id="queue" tabindex="-1" class="grid gap-5 lg:grid-cols-3">
  {#each COLUMNS as column}
    <section aria-labelledby={`col-${column.status}`} data-status={column.status}>
      <h2 id={`col-${column.status}`} class="mb-3 flex items-center gap-2 text-lg font-bold">
        {column.title}
        <span class="rounded-full bg-fog px-2.5 text-sm">{byStatus[column.status].length}</span>
      </h2>
      <ul class="flex flex-col gap-3">
        {#if !loaded}
          {#each [1, 2] as _}
            <li class="card flex flex-col gap-3 p-4" aria-hidden="true">
              <div class="skeleton h-8 w-20"></div>
              <div class="skeleton h-4 w-32"></div>
              <div class="skeleton h-10 w-full"></div>
            </li>
          {/each}
        {:else if byStatus[column.status].length === 0}
          <li class="rounded-card border-2 border-dashed border-line p-6 text-center text-sm text-muted">Nothing here</li>
        {/if}
        {#each byStatus[column.status] as order (order.id)}
          <li
            data-order={order.id}
            class={[
              'card animate-pop flex flex-col gap-1 border-2 p-4',
              order.status === 'ready' ? 'border-ok' : order.status === 'pending' ? 'border-accent/40' : 'border-transparent',
            ]}
          >
            <div class="flex items-baseline justify-between">
              <span class={['font-display text-4xl leading-none', order.status === 'ready' && 'text-ok']}>#{order.ticket}</span>
              <time class="text-sm text-muted" datetime={order.created_at}>{formatTime('en', order.created_at)}</time>
            </div>
            <span class="font-semibold">{order.guest_name || 'Guest'}</span>
            <span class="text-sm text-muted">
              {order.items.map((i) => `${i.drink_name} x${i.quantity}`).join(', ')}
            </span>
            <span class="text-sm font-semibold">{formatPrice('en', order.total)}</span>
            <div class="mt-2 flex gap-2">
              <button
                type="button"
                data-primary
                class="btn-primary flex-1"
                disabled={busy.has(order.id)}
                onclick={() => act(order, NEXT[order.status].action)}
                aria-label={`${NEXT[order.status].label}, ticket ${order.ticket}`}
              >
                {NEXT[order.status].label}
              </button>
              <button
                type="button"
                class="btn-danger"
                disabled={busy.has(order.id)}
                onclick={() => act(order, 'cancel')}
                aria-label={`Cancel ticket ${order.ticket}`}
              >
                Cancel
              </button>
            </div>
          </li>
        {/each}
      </ul>
    </section>
  {/each}
</div>
