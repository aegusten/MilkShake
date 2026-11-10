<script>
  import { page } from '$app/state';
</script>

<div class="card mx-auto mt-16 max-w-md p-8 text-center" role="alert">
  <p class="font-display text-5xl text-accent-strong">{page.status}</p>
  <p class="mt-2 font-semibold">{page.error?.message || 'Something went wrong on this screen.'}</p>
  <a class="btn-primary mt-4" href="/admin/orders">Back to orders</a>
</div>
