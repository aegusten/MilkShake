<script>
  import { useLocale } from '$lib/locale.svelte.js';

  let { order, finished, onnew } = $props();
  const i18n = useLocale();
</script>

<section
  data-testid="ticket-card"
  aria-labelledby="ticket-label"
  class={[
    'card flex flex-col items-center gap-2 border-4 p-6 text-center',
    order.status === 'ready' ? 'border-ok' : order.status === 'cancelled' ? 'border-accent-strong' : 'border-fog',
  ]}
>
  <p id="ticket-label" class="text-xs font-semibold uppercase tracking-widest text-muted">
    {i18n.t('ticket.label')}
  </p>
  <p class={['font-display text-7xl leading-none', order.status === 'ready' && 'text-ok']}>
    #{order.ticket}
  </p>
  <!-- Announced to screen readers whenever the status changes. -->
  <p class="text-lg font-bold" role="status" aria-live="polite">
    {i18n.t(`ticket.status.${order.status}`)}
  </p>
  {#if finished}
    <button type="button" class="btn-ghost mt-2" onclick={onnew}>{i18n.t('ticket.new')}</button>
  {:else}
    <p class="text-sm text-muted">{i18n.t('ticket.watch')}</p>
  {/if}
</section>
