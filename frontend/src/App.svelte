<script>
  import { onMount } from "svelte";
  import AdminPage from "./components/admin/AdminPage.svelte";
  import PublicPage from "./components/public/PublicPage.svelte";

  let isAdmin = false;
  let pathLabel = "";

  onMount(() => {
    const path = window.location.pathname;
    isAdmin = path.startsWith("/admin");
    pathLabel = path;
  });
</script>

{#if isAdmin}
  <AdminPage {pathLabel} />
{:else}
  <PublicPage />
{/if}
