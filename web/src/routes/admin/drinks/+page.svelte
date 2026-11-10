<script>
  import { onMount } from 'svelte';
  import { api } from '$lib/api.js';
  import { useAdmin } from '$lib/admin.svelte.js';
  import { formatPrice } from '$lib/i18n.js';

  const session = useAdmin();
  const TYPES = ['milkshake', 'cocktail', 'soft', 'other'];
  const CROP = 640;

  let drinks = $state([]);
  let masters = $state([]);
  let loaded = $state(false);
  let error = $state('');
  let saving = $state(false);
  let confirmDelete = $state(null);

  const emptyDrink = () => ({ id: null, name: '', description: '', price: 0, type: 'milkshake', item_master_ids: [], image_cover: '' });
  let form = $state(emptyDrink());
  let masterForm = $state({ id: null, name: '' });

  // Image cropping: the photo is dragged and zoomed inside a square frame,
  // then drawn to a 640px canvas and uploaded as a JPEG.
  let preview = $state('');
  let zoom = $state(1);
  let offset = $state({ x: 0, y: 0 });
  let dragFrom = null;

  function failed(response, fallback) {
    if (response.status === 401) {
      session.expired();
      return true;
    }
    if (!response.ok) {
      error = response.data?.detail || fallback;
      return true;
    }
    return false;
  }

  async function load() {
    const [d, m] = await Promise.all([api.drinks(), api.itemMasters()]);
    if (failed(d, 'Could not load drinks.') || failed(m, 'Could not load categories.')) return;
    drinks = d.data;
    masters = m.data;
    loaded = true;
  }

  function pickImage(file) {
    if (!file?.type.startsWith('image/')) {
      error = 'Choose an image file.';
      return;
    }
    error = '';
    preview = URL.createObjectURL(file);
    zoom = 1;
    offset = { x: 0, y: 0 };
  }

  function nudge(event) {
    const step = event.shiftKey ? 20 : 5;
    const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    const move = moves[event.key];
    if (!move) return;
    event.preventDefault();
    offset = { x: offset.x + move[0], y: offset.y + move[1] };
  }

  async function uploadCrop() {
    const img = new Image();
    img.src = preview;
    await img.decode();
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = CROP;
    const scale = Math.max(CROP / img.width, CROP / img.height) * zoom;
    const w = img.width * scale;
    const h = img.height * scale;
    // Offsets are measured on the on-screen frame; scale them to the canvas.
    const frame = document.getElementById('crop-frame').offsetWidth || CROP;
    const ratio = CROP / frame;
    canvas.getContext('2d').drawImage(img, (CROP - w) / 2 + offset.x * ratio, (CROP - h) / 2 + offset.y * ratio, w, h);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.88));
    const response = await api.uploadImage(new File([blob], 'drink.jpg', { type: 'image/jpeg' }));
    if (failed(response, 'Upload failed.')) return;
    form.image_cover = response.data.url;
    preview = '';
  }

  async function saveDrink(event) {
    event.preventDefault();
    error = '';
    if (!form.name.trim()) return (error = 'Name is required.');
    if (!form.item_master_ids.length) return (error = 'Pick at least one category.');
    saving = true;
    const payload = {
      name: form.name.trim(),
      description: form.description.trim().slice(0, 160) || null,
      price: Number(form.price) || 0,
      type: form.type,
      image_cover: form.image_cover || null,
      item_master_ids: form.item_master_ids,
    };
    const response = form.id ? await api.updateDrink(form.id, payload) : await api.createDrink(payload);
    saving = false;
    if (failed(response, 'Save failed.')) return;
    form = emptyDrink();
    preview = '';
    await load();
  }

  function editDrink(drink) {
    form = {
      id: drink.id,
      name: drink.name,
      description: drink.description ?? '',
      price: drink.price,
      type: drink.type ?? 'other',
      item_master_ids: (drink.item_masters ?? []).map((m) => m.id),
      image_cover: drink.image_cover ?? '',
    };
    preview = '';
    document.getElementById('drink-name')?.focus();
  }

  async function removeDrink(id) {
    if (confirmDelete !== `drink:${id}`) return (confirmDelete = `drink:${id}`);
    confirmDelete = null;
    if (failed(await api.deleteDrink(id), 'Delete failed.')) return;
    if (form.id === id) form = emptyDrink();
    await load();
  }

  async function saveMaster(event) {
    event.preventDefault();
    error = '';
    if (!masterForm.name.trim()) return (error = 'Category name is required.');
    const payload = { name: masterForm.name.trim() };
    const response = masterForm.id
      ? await api.updateItemMaster(masterForm.id, payload)
      : await api.createItemMaster(payload);
    if (failed(response, 'Save failed.')) return;
    masterForm = { id: null, name: '' };
    await load();
  }

  async function removeMaster(id) {
    if (confirmDelete !== `master:${id}`) return (confirmDelete = `master:${id}`);
    confirmDelete = null;
    if (failed(await api.deleteItemMaster(id), 'Delete failed.')) return;
    await load();
  }

  onMount(load);
</script>

<h1 class="mb-5 font-display text-5xl">Menu</h1>

{#if error}
  <p class="card mb-4 p-4 font-semibold text-accent-strong" role="alert">{error}</p>
{/if}

<div class="grid gap-6 lg:grid-cols-[minmax(0,26rem)_1fr]">
  <div class="flex flex-col gap-6">
    <form class="card flex flex-col gap-4 p-5" onsubmit={saveDrink} novalidate aria-labelledby="drink-form-title">
      <h2 id="drink-form-title" class="text-xl font-bold">{form.id ? 'Edit drink' : 'Add a drink'}</h2>
      <label class="label">
        Name
        <input id="drink-name" class="field" required bind:value={form.name} />
      </label>
      <label class="label">
        Description
        <textarea class="field" rows="3" maxlength="160" bind:value={form.description}></textarea>
        <span class="text-xs font-normal text-muted">{form.description.length}/160</span>
      </label>
      <div class="grid grid-cols-2 gap-3">
        <label class="label">
          Price (UZS)
          <input class="field" type="number" min="0" step="500" bind:value={form.price} />
        </label>
        <label class="label">
          Type
          <select class="field" bind:value={form.type}>
            {#each TYPES as t}<option value={t}>{t}</option>{/each}
          </select>
        </label>
      </div>
      <fieldset class="flex flex-col gap-2">
        <legend class="mb-1 text-sm font-semibold">Categories</legend>
        {#if masters.length === 0}
          <p class="text-sm text-muted">Add a category below first.</p>
        {/if}
        <div class="flex flex-wrap gap-2">
          {#each masters as m (m.id)}
            <label class="flex min-h-11 cursor-pointer items-center gap-2 rounded-full border border-line px-4 has-checked:border-ink has-checked:bg-ink has-checked:text-white">
              <input type="checkbox" class="sr-only" value={m.id} bind:group={form.item_master_ids} />
              {m.name}
            </label>
          {/each}
        </div>
      </fieldset>

      <fieldset class="flex flex-col gap-3">
        <legend class="mb-1 text-sm font-semibold">Photo</legend>
        {#if preview}
          <!-- A button so it is focusable and announced; arrow keys move the photo. -->
          <button
            type="button"
            id="crop-frame"
            class="relative block aspect-square w-full cursor-grab touch-none overflow-hidden rounded-xl bg-fog active:cursor-grabbing"
            aria-label="Photo position. Drag, or use the arrow keys to move the photo."
            onkeydown={nudge}
            onpointerdown={(e) => (dragFrom = { x: e.clientX - offset.x, y: e.clientY - offset.y })}
            onpointermove={(e) => dragFrom && (offset = { x: e.clientX - dragFrom.x, y: e.clientY - dragFrom.y })}
            onpointerup={() => (dragFrom = null)}
            onpointerleave={() => (dragFrom = null)}
          >
            <img
              src={preview}
              alt=""
              draggable="false"
              class="pointer-events-none absolute inset-0 size-full object-cover select-none"
              style:transform={`translate(${offset.x}px, ${offset.y}px) scale(${zoom})`}
            />
          </button>
          <label class="label">
            Zoom
            <input type="range" min="1" max="2.5" step="0.01" bind:value={zoom} />
          </label>
          <div class="flex gap-2">
            <button type="button" class="btn-primary" onclick={uploadCrop}>Use this photo</button>
            <button type="button" class="btn-ghost" onclick={() => (preview = '')}>Discard</button>
          </div>
        {:else}
          <label
            class="flex cursor-pointer flex-col items-center gap-1 rounded-xl border-2 border-dashed border-line p-6 text-center text-sm focus-within:border-ink"
            ondragover={(e) => e.preventDefault()}
            ondrop={(e) => {
              e.preventDefault();
              pickImage(e.dataTransfer.files[0]);
            }}
          >
            <span class="font-semibold">Drop a photo, or choose one</span>
            <span class="text-muted">PNG, JPEG, GIF or WebP up to 5 MB</span>
            <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="sr-only" onchange={(e) => pickImage(e.currentTarget.files[0])} />
          </label>
        {/if}
        {#if form.image_cover && !preview}
          <div class="flex items-center gap-3">
            <img src={form.image_cover} alt="Current" class="size-16 rounded-lg object-cover" />
            <button type="button" class="btn-ghost" onclick={() => (form.image_cover = '')}>Remove photo</button>
          </div>
        {/if}
      </fieldset>

      <div class="flex gap-2">
        <button type="submit" class="btn-primary" disabled={saving}>{form.id ? 'Save changes' : 'Add drink'}</button>
        {#if form.id}
          <button type="button" class="btn-ghost" onclick={() => (form = emptyDrink())}>Cancel</button>
        {/if}
      </div>
    </form>

    <form class="card flex flex-col gap-4 p-5" onsubmit={saveMaster} novalidate aria-labelledby="master-form-title">
      <h2 id="master-form-title" class="text-xl font-bold">{masterForm.id ? 'Rename category' : 'Add a category'}</h2>
      <label class="label">
        Name
        <input id="master-name" class="field" required bind:value={masterForm.name} />
      </label>
      <div class="flex gap-2">
        <button type="submit" class="btn-primary">{masterForm.id ? 'Save' : 'Add category'}</button>
        {#if masterForm.id}
          <button type="button" class="btn-ghost" onclick={() => (masterForm = { id: null, name: '' })}>Cancel</button>
        {/if}
      </div>
    </form>
  </div>

  <div class="flex flex-col gap-6">
    <section aria-labelledby="drinks-title">
      <h2 id="drinks-title" class="mb-3 text-lg font-bold">Drinks <span class="text-muted">({drinks.length})</span></h2>
      <ul class="flex flex-col gap-3">
        {#if !loaded}
          {#each [1, 2, 3] as _}
            <li class="card flex gap-4 p-4" aria-hidden="true">
              <div class="skeleton size-16"></div>
              <div class="flex flex-1 flex-col gap-2"><div class="skeleton h-5 w-40"></div><div class="skeleton h-4 w-64"></div></div>
            </li>
          {/each}
        {/if}
        {#each drinks as drink (drink.id)}
          <li class="card flex flex-wrap items-center gap-4 p-4">
            {#if drink.image_cover}
              <img src={drink.image_cover} alt="" class="size-16 rounded-lg object-cover" loading="lazy" />
            {:else}
              <div class="size-16 rounded-lg bg-fog" aria-hidden="true"></div>
            {/if}
            <div class="min-w-0 flex-1">
              <p class="font-bold">{drink.name}</p>
              <p class="text-sm text-muted">
                {formatPrice('en', drink.price)} · {(drink.item_masters ?? []).map((m) => m.name).join(', ') || 'No category'}
              </p>
            </div>
            <div class="flex gap-2">
              <button type="button" class="btn-ghost" onclick={() => editDrink(drink)} aria-label={`Edit ${drink.name}`}>Edit</button>
              <button
                type="button"
                class={confirmDelete === `drink:${drink.id}` ? 'btn-accent' : 'btn-danger'}
                onclick={() => removeDrink(drink.id)}
                onblur={() => confirmDelete === `drink:${drink.id}` && (confirmDelete = null)}
                aria-label={confirmDelete === `drink:${drink.id}` ? `Confirm removing ${drink.name}` : `Remove ${drink.name}`}
              >
                {confirmDelete === `drink:${drink.id}` ? 'Sure?' : 'Remove'}
              </button>
            </div>
          </li>
        {/each}
      </ul>
    </section>

    <section aria-labelledby="masters-title">
      <h2 id="masters-title" class="mb-3 text-lg font-bold">Categories</h2>
      <ul class="flex flex-wrap gap-2">
        {#each masters as m (m.id)}
          <li class="card flex items-center gap-1 py-1 pr-1 pl-4">
            <span class="mr-2 font-semibold">{m.name}</span>
            <button type="button" class="btn-ghost min-h-10" onclick={() => (masterForm = { id: m.id, name: m.name })} aria-label={`Rename ${m.name}`}>Rename</button>
            <button
              type="button"
              class={['min-h-10', confirmDelete === `master:${m.id}` ? 'btn-accent' : 'btn-danger']}
              onclick={() => removeMaster(m.id)}
              onblur={() => confirmDelete === `master:${m.id}` && (confirmDelete = null)}
              aria-label={confirmDelete === `master:${m.id}` ? `Confirm deleting ${m.name}` : `Delete ${m.name}`}
            >
              {confirmDelete === `master:${m.id}` ? 'Sure?' : 'Delete'}
            </button>
          </li>
        {/each}
      </ul>
    </section>
  </div>
</div>
