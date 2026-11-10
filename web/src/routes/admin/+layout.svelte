<script>
  import { page } from '$app/state';
  import { api } from '$lib/api.js';
  import { provideAdmin } from '$lib/admin.svelte.js';

  let { children } = $props();
  const session = provideAdmin();

  let email = $state('');
  let password = $state('');
  let error = $state('');
  let busy = $state(false);

  const tabs = [
    { href: '/admin/orders', label: 'Orders' },
    { href: '/admin/drinks', label: 'Menu' },
  ];

  async function login(event) {
    event.preventDefault();
    error = '';
    busy = true;
    const response = await api.login(email.trim().toLowerCase(), password);
    busy = false;
    if (!response.ok) {
      error = response.data?.detail || 'Sign-in failed.';
      return;
    }
    password = '';
    session.notice = '';
    session.loggedIn = true;
  }
</script>

<svelte:head>
  <title>Staff | MilkShake</title>
  <meta name="robots" content="noindex" />
</svelte:head>

{#if !session.loggedIn}
  <main class="mx-auto grid min-h-screen max-w-5xl items-center gap-10 px-6 py-10 md:grid-cols-2">
    <div>
      <p class="text-xs font-bold uppercase tracking-widest text-accent-strong">Staff</p>
      <h1 class="font-display text-6xl">Sign in to the bar</h1>
      <p class="mt-2 text-muted">Run the order queue and edit the menu.</p>
    </div>
    <form class="card flex flex-col gap-4 p-6" onsubmit={login}>
      <label class="label">
        Email
        <input class="field" type="email" autocomplete="username" required bind:value={email} />
      </label>
      <label class="label">
        Password
        <input class="field" type="password" autocomplete="current-password" required bind:value={password} />
      </label>
      {#if error || session.notice}
        <p class="font-semibold text-accent-strong" role="alert">{error || session.notice}</p>
      {/if}
      <button type="submit" class="btn-primary" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
    </form>
  </main>
{:else}
  <header class="sticky top-0 z-30 border-b border-line bg-canvas/90 backdrop-blur">
    <div class="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3">
      <span class="font-display text-2xl">MilkShake staff</span>
      <nav aria-label="Staff sections" class="flex gap-1">
        {#each tabs as tab}
          <a
            href={tab.href}
            aria-current={page.url.pathname.startsWith(tab.href) ? 'page' : undefined}
            class={[
              'btn min-h-10',
              page.url.pathname.startsWith(tab.href) ? 'bg-ink text-white' : 'text-ink hover:bg-fog',
            ]}
          >
            {tab.label}
          </a>
        {/each}
      </nav>
      <a class="btn-ghost ml-auto min-h-10" href="/display" target="_blank" rel="noopener">TV display</a>
      <button type="button" class="btn-ghost min-h-10" onclick={session.logout}>Log out</button>
    </div>
  </header>
  <main class="mx-auto max-w-7xl px-4 py-6">
    {@render children()}
  </main>
{/if}
