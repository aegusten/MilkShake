<script>
  export let adminOrders = [];
  export let ordersError = "";
  export let ordersLoading = false;
  export let onRefresh = null;

  const formatPrice = (value) =>
    new Intl.NumberFormat("uz-UZ").format(value) + " UZS";

  const formatTime = (value) => {
    if (!value) {
      return "";
    }
    const date = new Date(value);
    return new Intl.DateTimeFormat("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "short",
    }).format(date);
  };

  const itemCount = (order) =>
    (order.items || []).reduce((sum, item) => sum + (item.quantity || 0), 0);
</script>

<div class="admin-orders">
  <div class="admin-orders-head">
    <h2>Incoming orders</h2>
    <div class="admin-actions">
      <span>Live queue overview</span>
      {#if onRefresh}
        <button class="ghost" type="button" on:click={onRefresh} disabled={ordersLoading}>
          {ordersLoading ? "Refreshing..." : "Refresh"}
        </button>
      {/if}
    </div>
  </div>
  <div class="admin-orders-grid">
    {#if ordersError}
      <div class="admin-empty">{ordersError}</div>
    {:else if ordersLoading}
      <div class="admin-empty">Loading orders...</div>
    {:else}
    {#if adminOrders.length === 0}
      <div class="admin-empty">No orders yet.</div>
    {:else}
      {#each adminOrders as order}
        <div class={`admin-order-card status-${order.status}`}>
          <div>
            <strong>{order.id}</strong>
            <span>{order.guest_name} - {itemCount(order)} items</span>
            <span>
              {(order.items || []).map((item) => `${item.drink_name} x${item.quantity}`).join(", ")}
            </span>
          </div>
          <div class="admin-order-meta">
            <span>{formatPrice(order.total || 0)}</span>
            <span>{formatTime(order.created_at)}</span>
          </div>
          <div class="admin-order-actions">
            <button class="ghost" type="button">Mark ready</button>
            <button class="ghost danger" type="button">Cancel</button>
          </div>
        </div>
      {/each}
    {/if}
    {/if}
  </div>
</div>
