<script>
  import { onMount } from "svelte";
  import QRCode from "qrcode";

  let targetUrl = "";
  let qrDataUrl = "";
  let error = "";
  let copied = false;
  let showLocalTip = false;

  const setDefaultUrl = () => {
    const origin = window.location.origin;
    targetUrl = origin.endsWith("/") ? origin : `${origin}/`;
  };

  const generateQr = async () => {
    error = "";
    copied = false;
    if (!targetUrl) {
      error = "Enter a URL to generate a QR code.";
      qrDataUrl = "";
      return;
    }
    try {
      qrDataUrl = await QRCode.toDataURL(targetUrl, {
        width: 280,
        margin: 1,
        color: {
          dark: "#111111",
          light: "#ffffff",
        },
      });
    } catch (err) {
      error = "Unable to generate a QR code.";
      qrDataUrl = "";
    }
  };

  const copyUrl = async () => {
    copied = false;
    try {
      await navigator.clipboard.writeText(targetUrl);
      copied = true;
    } catch (err) {
      error = "Copy failed. Select the URL and copy it manually.";
    }
  };

  onMount(() => {
    setDefaultUrl();
    generateQr();
    const host = window.location.hostname;
    showLocalTip = host === "localhost" || host === "127.0.0.1";
  });
</script>

<div class="page qr-page">
  <header class="topbar sticky">
    <div class="brand-block">
      <span class="logo"></span>
      <div>
        <span class="brand">MilkShake</span>
        <span class="tag">Local QR access</span>
      </div>
    </div>
    <div class="topbar-actions">
      <a class="ghost link-pill" href="/">Back to menu</a>
      <a class="ghost link-pill" href="/admin">Admin</a>
    </div>
  </header>

  <main class="qr-shell">
    <section class="qr-hero">
      <span class="eyebrow">Share</span>
      <h1>Scan to open the menu</h1>
      <p class="qr-meta">
        Generate a QR code for the menu URL, then scan it with a phone on the same
        network.
      </p>
      {#if showLocalTip}
        <p class="qr-meta">
          Tip: switch to your computer's LAN IP in the URL so phones can reach it.
        </p>
      {/if}
    </section>

    <section class="qr-card">
      <div class="qr-preview">
        {#if qrDataUrl}
          <img src={qrDataUrl} alt="QR code for menu URL" />
        {:else}
          <div class="qr-empty">QR code will appear here.</div>
        {/if}
      </div>

      <div class="qr-input">
        <label for="qr-url">Menu URL</label>
        <input id="qr-url" type="url" bind:value={targetUrl} />
      </div>

      <div class="qr-actions">
        <button class="primary" type="button" on:click={generateQr}>
          Generate QR
        </button>
        <button class="ghost" type="button" on:click={copyUrl}>
          Copy URL
        </button>
        <a class="ghost link-pill" href={targetUrl} rel="noreferrer">
          Open URL
        </a>
      </div>

      {#if copied}
        <div class="qr-status">Copied to clipboard.</div>
      {/if}
      {#if error}
        <div class="qr-status">{error}</div>
      {/if}
      <div class="qr-link">{targetUrl}</div>
    </section>
  </main>
</div>
