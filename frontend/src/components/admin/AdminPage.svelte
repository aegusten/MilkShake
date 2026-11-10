<script>
  import { onDestroy, onMount } from "svelte";
  import {
    changeOrderStatus,
    isAdminLoggedIn,
    loginAdmin,
    logoutAdmin,
    streamAdminOrders,
  } from "../../api/index.js";
  import AdminOrders from "./AdminOrders.svelte";
  import AdminDrinks from "./AdminDrinks.svelte";

  export let pathLabel = "";

  const OPEN = ["pending", "accepted", "ready"];

  let adminLoggedIn = false;
  let adminEmail = "";
  let adminPassword = "";
  let adminError = "";
  let adminTab = "orders";

  let adminOrders = [];
  let ordersError = "";
  let streamStatus = "connecting";
  let busyIds = new Set();
  let stopStream = null;

  // Replace by id, drop orders that left the open states, keep oldest first
  // so the next ticket to make is at the top.
  const upsertOrder = (order) => {
    const rest = adminOrders.filter((o) => o.id !== order.id);
    adminOrders = (OPEN.includes(order.status) ? [...rest, order] : rest).sort(
      (a, b) => new Date(a.created_at) - new Date(b.created_at)
    );
  };

  const handleUnauthorized = (message = "Session expired. Please log in again.") => {
    stopStream?.();
    stopStream = null;
    adminLoggedIn = false;
    adminOrders = [];
    adminError = message;
  };

  const startStream = () => {
    stopStream?.();
    streamStatus = "connecting";
    stopStream = streamAdminOrders({
      onEvent: ({ event, data }) => {
        if (event === "snapshot") {
          adminOrders = [];
          data.orders.forEach(upsertOrder);
        } else if (event === "order") {
          upsertOrder(data.order);
        }
      },
      onStatus: (status) => (streamStatus = status),
      onUnauthorized: () => handleUnauthorized(),
    });
  };

  const handleAction = async (order, action) => {
    ordersError = "";
    busyIds = new Set([...busyIds, order.id]);
    const response = await changeOrderStatus(order.id, action);
    busyIds.delete(order.id);
    busyIds = new Set(busyIds);
    if (response.status === 401) {
      handleUnauthorized();
      return;
    }
    if (!response.ok) {
      ordersError = response.data?.detail || "Could not update the order.";
      return;
    }
    // The stream will echo this too; applying it now keeps the button snappy.
    upsertOrder(response.data);
  };

  const handleLogin = async () => {
    adminError = "";
    const response = await loginAdmin(
      adminEmail.trim().toLowerCase(),
      adminPassword
    );
    if (!response.ok || !response.data?.access_token) {
      adminError = response.data?.detail || "Login failed.";
      return;
    }
    adminLoggedIn = true;
    adminPassword = "";
    startStream();
  };

  const handleLogout = () => {
    stopStream?.();
    stopStream = null;
    logoutAdmin();
    adminLoggedIn = false;
    adminOrders = [];
    adminError = "";
  };

  onMount(() => {
    if (isAdminLoggedIn()) {
      adminLoggedIn = true;
      startStream();
    }
  });

  onDestroy(() => stopStream?.());
</script>

<div class="admin-shell admin-shell-wide">
  <header class="admin-header">
    <span class="brand">MilkShake Admin</span>
    <span class="path">Path: {pathLabel}</span>
    {#if adminLoggedIn}
      <button class="ghost" type="button" on:click={handleLogout}>Log out</button>
    {/if}
  </header>
  {#if !adminLoggedIn}
    <section class="admin-auth">
      <div class="admin-auth-panel">
        <span class="eyebrow">Admin access</span>
        <h1>Sign in to the desk</h1>
        <p>Use your admin credentials to unlock orders and drinks.</p>
        <div class="admin-auth-meta">
          <div>
            <strong>Orders</strong>
            <span>Track live queue activity</span>
          </div>
          <div>
            <strong>Drinks</strong>
            <span>Create drinks and assign item masters</span>
          </div>
        </div>
      </div>
      <div class="admin-auth-card">
        <h2>Secure sign-in</h2>
        <p>Enter your admin credentials to continue.</p>
        <form class="admin-form" on:submit|preventDefault={handleLogin}>
          <label>
            Email
            <input
              type="email"
              placeholder="admin@milkshake.local"
              bind:value={adminEmail}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              placeholder="Enter password"
              bind:value={adminPassword}
              required
            />
          </label>
          <button type="submit">Sign in</button>
        </form>
        {#if adminError}
          <span class="admin-error">{adminError}</span>
        {/if}
        <span class="admin-note">Admin login is managed in Postgres.</span>
      </div>
    </section>
  {:else}
    <section class="admin-dashboard">
      <div class="admin-dashboard-head">
        <div>
          <h1>MilkShake Admin Desk</h1>
          <p>Orders stay front and center. Drinks live in the tools panel.</p>
        </div>
        <div class="admin-tabs">
          <button
            type="button"
            class={`pill ${adminTab === "orders" ? "is-active" : ""}`}
            on:click={() => (adminTab = "orders")}
          >
            Orders
          </button>
          <button
            type="button"
            class={`pill ${adminTab === "drinks" ? "is-active" : ""}`}
            on:click={() => (adminTab = "drinks")}
          >
            Drinks
          </button>
        </div>
      </div>

      {#if adminTab === "orders"}
        <AdminOrders
          {adminOrders}
          {ordersError}
          {streamStatus}
          {busyIds}
          onAction={handleAction}
        />
      {:else}
        <AdminDrinks
          {adminLoggedIn}
          on:unauthorized={() => handleUnauthorized()}
        />
      {/if}
    </section>
  {/if}
</div>
