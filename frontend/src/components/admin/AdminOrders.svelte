<script>
  export let adminOrders = [];
  export let ordersError = "";
  export let streamStatus = "connecting";
  export let busyIds = new Set();
  export let onAction = null;

  // The forward button each status offers. Cancel is offered on all of them.
  const NEXT = {
    pending: { action: "accept", label: "Accept" },
    accepted: { action: "ready", label: "Mark ready" },
    ready: { action: "complete", label: "Picked up" },
  };
  const COLUMNS = [
    { status: "pending", title: "New" },
    { status: "accepted", title: "Making" },
    { status: "ready", title: "Ready for pickup" },
  ];
  const STREAM_LABEL = {
    live: "Live",
    reconnecting: "Reconnecting...",
    connecting: "Connecting...",
  };

  const formatPrice = (value) =>
    new Intl.NumberFormat("uz-UZ").format(value) + " UZS";

  const formatTime = (value) =>
    value
      ? new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit" }).format(
          new Date(value)
        )
      : "";

  const itemsLine = (order) =>
    (order.items || []).map((item) => `${item.drink_name} x${item.quantity}`).join(", ");

  $: byStatus = Object.fromEntries(
    COLUMNS.map(({ status }) => [status, adminOrders.filter((o) => o.status === status)])
  );
</script>

<div class="admin-orders">
  <div class="admin-orders-head">
    <h2>Order queue</h2>
    <div class="admin-actions">
      <span class={`stream-dot stream-${streamStatus}`}></span>
      <span data-testid="stream-status">{STREAM_LABEL[streamStatus]}</span>
      <a class="ghost" href="/display" target="_blank" rel="noopener">Open TV display</a>
    </div>
  </div>

  {#if ordersError}
    <div class="admin-empty">{ordersError}</div>
  {/if}

  <div class="queue-columns">
    {#each COLUMNS as column}
      <section class="queue-column" data-status={column.status}>
        <h3>{column.title} <span class="count">{byStatus[column.status].length}</span></h3>
        {#if byStatus[column.status].length === 0}
          <div class="admin-empty">Nothing here.</div>
        {/if}
        {#each byStatus[column.status] as order (order.id)}
          <article class={`admin-order-card status-${order.status}`}>
            <div class="ticket-row">
              <span class="ticket">#{order.ticket}</span>
              <span class="order-time">{formatTime(order.created_at)}</span>
            </div>
            <span class="guest">{order.guest_name || "Guest"}</span>
            <span class="items">{itemsLine(order)}</span>
            <span class="total">{formatPrice(order.total || 0)}</span>
            {#if onAction}
              <div class="admin-order-actions">
                <button
                  type="button"
                  disabled={busyIds.has(order.id)}
                  on:click={() => onAction(order, NEXT[order.status].action)}
                >
                  {NEXT[order.status].label}
                </button>
                <button
                  class="ghost danger"
                  type="button"
                  disabled={busyIds.has(order.id)}
                  on:click={() => onAction(order, "cancel")}
                >
                  Cancel
                </button>
              </div>
            {/if}
          </article>
        {/each}
      </section>
    {/each}
  </div>
</div>

<style>
  .queue-columns {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }
  @media (max-width: 900px) {
    .queue-columns {
      grid-template-columns: 1fr;
    }
  }
  .queue-column h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 12px;
  }
  .count {
    font-size: 0.8rem;
    background: var(--fog);
    border-radius: 999px;
    padding: 2px 10px;
  }
  .admin-order-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 12px;
  }
  .ticket-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
  }
  .ticket {
    font-family: var(--font-display);
    font-size: 2rem;
    line-height: 1;
  }
  .order-time,
  .items {
    color: var(--muted);
    font-size: 0.9rem;
  }
  .guest {
    font-weight: 600;
  }
  .admin-order-actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
  }
  .stream-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #c9c9c9;
  }
  .stream-live {
    background: #22c55e;
  }
  .stream-reconnecting {
    background: #f59e0b;
  }
  .status-ready .ticket {
    color: #16a34a;
  }
</style>
