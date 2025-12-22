<script>
  export let adminOrders = [];

  const formatPrice = (value) =>
    new Intl.NumberFormat("uz-UZ").format(value) + " UZS";
</script>

<div class="admin-orders">
  <div class="admin-orders-head">
    <h2>Incoming orders</h2>
    <span>Live queue overview</span>
  </div>
  <div class="admin-orders-grid">
    {#if adminOrders.length === 0}
      <div class="admin-empty">No orders yet.</div>
    {:else}
      {#each adminOrders as order}
        <div class={`admin-order-card status-${order.status}`}>
          <div>
            <strong>{order.id}</strong>
            <span>{order.name} - {order.items} items</span>
          </div>
          <div class="admin-order-meta">
            <span>{formatPrice(order.total || 0)}</span>
            <span>{order.time}</span>
          </div>
          <div class="admin-order-actions">
            <button class="ghost" type="button">Mark ready</button>
            <button class="ghost danger" type="button">Cancel</button>
          </div>
        </div>
      {/each}
    {/if}
  </div>
</div>
