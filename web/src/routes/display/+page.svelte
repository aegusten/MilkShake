<script>
  import { onDestroy, onMount } from 'svelte';
  import { liveEvents } from '$lib/api.js';
  import { useLocale } from '$lib/locale.svelte.js';
  import LangSwitch from '$lib/components/LangSwitch.svelte';

  // Pickup TV. Built to run unattended in a kiosk browser for days: every
  // event carries the full ready list, so the screen never merges state and
  // cannot drift, and every reconnect starts with a fresh list.
  const i18n = useLocale();
  let tickets = $state([]);
  let connected = $state(false);
  let stop = null;

  onMount(() => {
    stop = liveEvents(
      '/api/stream/display',
      { tickets: (data) => (tickets = data.tickets) },
      (status) => (connected = status === 'live')
    );
  });
  onDestroy(() => stop?.());
</script>

<svelte:head>
  <title>{i18n.t('display.title')} | MilkShake</title>
</svelte:head>

<main class="min-h-screen bg-tv px-[5vw] py-[4vh] text-tv-text">
  <header class="mb-[5vh] flex items-center gap-[2vw]">
    <span class="font-display text-[4vh] text-accent">MilkShake</span>
    <h1 class="font-display text-[6vh] tracking-wide">{i18n.t('display.title')}</h1>
    <div class="ml-auto flex items-center gap-4">
      <LangSwitch dark />
      <span
        class={['size-[1.4vh] min-h-3 min-w-3 rounded-full', connected ? 'bg-green-500' : 'bg-neutral-600']}
        role="img"
        aria-label={connected ? 'Live' : 'Reconnecting'}
      ></span>
    </div>
  </header>

  {#if tickets.length === 0}
    <p class="text-[3.5vh] text-tv-muted">{i18n.t('display.empty')}</p>
  {:else}
    <ul class="grid grid-cols-[repeat(auto-fill,minmax(22vh,1fr))] gap-[3vh]" aria-live="polite">
      {#each tickets as t, i (t.ticket)}
        <li
          class={[
            'animate-pop rounded-[2vh] py-[3vh] text-center font-display text-[12vh] leading-none',
            i === 0 ? 'bg-accent text-ink' : 'bg-tv-tile text-tv-text',
          ]}
        >
          {t.ticket}
        </li>
      {/each}
    </ul>
  {/if}
</main>
