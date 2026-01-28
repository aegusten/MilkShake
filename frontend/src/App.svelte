<script>
  import { onMount } from "svelte";
  import AdminPage from "./components/admin/AdminPage.svelte";
  import PublicPage from "./components/public/PublicPage.svelte";
  import QrPage from "./components/public/QrPage.svelte";

  let route = "public";
  let pathLabel = "";

  const resolveRoute = () => {
    const path = window.location.pathname;
    pathLabel = path;
    if (path.startsWith("/admin")) {
      route = "admin";
      return;
    }
    if (path.startsWith("/qr")) {
      route = "qr";
      return;
    }
    route = "public";
  };

  onMount(() => {
    resolveRoute();
  });
</script>

{#if route === "admin"}
  <AdminPage {pathLabel} />
{:else if route === "qr"}
  <QrPage />
{:else}
  <PublicPage />
{/if}
