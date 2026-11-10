<script>
  import { onDestroy, onMount } from "svelte";
  import { liveEvents } from "../../api/index.js";

  // Pickup TV. Built to run unattended in a kiosk browser for days: every
  // event carries the full ready list, so the screen never merges state and
  // cannot drift, and every reconnect starts with a fresh list.
  let tickets = [];
  let connected = false;
  let stop = null;

  onMount(() => {
    stop = liveEvents(
      "/api/stream/display",
      { tickets: (data) => (tickets = data.tickets) },
      (status) => (connected = status === "live")
    );
  });

  onDestroy(() => stop?.());
</script>

<main class="tv">
  <header>
    <span class="brand">MilkShake</span>
    <span class="title">Ready for pickup</span>
    <span class={`dot ${connected ? "on" : ""}`} aria-hidden="true"></span>
  </header>

  {#if tickets.length === 0}
    <p class="empty">Your number will appear here when your drink is ready.</p>
  {:else}
    <ul class="grid">
      {#each tickets as t, i (t.ticket)}
        <li class:newest={i === 0}>{t.ticket}</li>
      {/each}
    </ul>
  {/if}
</main>

<style>
  .tv {
    min-height: 100vh;
    background: #0c0c0d;
    color: #f5f5f5;
    padding: 4vh 5vw;
    box-sizing: border-box;
    font-family: var(--font-body);
  }
  header {
    display: flex;
    align-items: center;
    gap: 2vw;
    margin-bottom: 5vh;
  }
  .brand {
    font-family: var(--font-display);
    font-size: 4vh;
    color: var(--accent);
  }
  .title {
    font-family: var(--font-display);
    font-size: 6vh;
    letter-spacing: 0.04em;
  }
  .dot {
    margin-left: auto;
    width: 1.4vh;
    height: 1.4vh;
    border-radius: 50%;
    background: #555;
  }
  .dot.on {
    background: #22c55e;
  }
  .empty {
    font-size: 3.5vh;
    color: #9a9aa0;
  }
  .grid {
    list-style: none;
    padding: 0;
    margin: 0;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(22vh, 1fr));
    gap: 3vh;
  }
  li {
    font-family: var(--font-display);
    font-size: 12vh;
    line-height: 1;
    text-align: center;
    padding: 3vh 0;
    border-radius: 2vh;
    background: #1c1c1f;
    animation: pop 400ms ease-out;
  }
  li.newest {
    background: var(--accent);
    color: #fff;
  }
  @keyframes pop {
    from {
      transform: scale(0.85);
      opacity: 0;
    }
    to {
      transform: scale(1);
      opacity: 1;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    li {
      animation: none;
    }
  }
</style>
