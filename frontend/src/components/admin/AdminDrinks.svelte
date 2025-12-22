<script>
  import {
    fetchItemMasters,
    fetchDrinks,
    createItemMaster,
    updateItemMaster,
    deleteItemMaster as removeItemMaster,
    createDrink,
    updateDrink,
    deleteDrink,
    uploadImage,
    API_BASE,
  } from "../../api/index.js";

  export let adminId = "";

  let drinks = [];
  let itemMasters = [];
  let adminError = "";
  let adminEditingId = null;
  let itemMasterEditingId = null;
  let hasLoaded = false;
  let imageFile = null;
  let imagePreview = "";
  let imageZoom = 1;
  let imageOffset = { x: 0, y: 0 };
  let isDragging = false;
  let dragStart = { x: 0, y: 0 };
  let imageLoaded = false;

  let adminForm = {
    name: "",
    detail: "",
    price: 0,
    type: "other",
    item_master_ids: [],
    image_cover: "",
  };

  let itemMasterForm = {
    name: "",
  };

  const loadItemMasters = async () => {
    const response = await fetchItemMasters();
    if (!response.ok) {
      return;
    }
    itemMasters = response.data || [];
  };

  const loadDrinks = async () => {
    const response = await fetchDrinks();
    if (!response.ok) {
      return;
    }
    drinks = response.data || [];
  };

  const loadCatalog = async () => {
    await Promise.all([loadItemMasters(), loadDrinks()]);
  };

  const resetAdminForm = () => {
    adminForm = {
      name: "",
      detail: "",
      price: 0,
      type: "other",
      item_master_ids: [],
      image_cover: "",
    };
    adminEditingId = null;
    clearImage();
  };

  const resetItemMasterForm = () => {
    itemMasterForm = {
      name: "",
    };
    itemMasterEditingId = null;
  };

  const clearImage = () => {
    imageFile = null;
    imagePreview = "";
    imageZoom = 1;
    imageOffset = { x: 0, y: 0 };
    imageLoaded = false;
  };

  const handleImageFile = (file) => {
    if (!file || !file.type.startsWith("image/")) {
      adminError = "Please drop an image file.";
      return;
    }
    adminError = "";
    imageFile = file;
    imagePreview = URL.createObjectURL(file);
    imageZoom = 1;
    imageOffset = { x: 0, y: 0 };
    imageLoaded = true;
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    handleImageFile(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    handleImageFile(file);
  };

  const handlePointerDown = (event) => {
    if (!imageLoaded) {
      return;
    }
    isDragging = true;
    dragStart = {
      x: event.clientX - imageOffset.x,
      y: event.clientY - imageOffset.y,
    };
  };

  const handlePointerMove = (event) => {
    if (!isDragging) {
      return;
    }
    imageOffset = {
      x: event.clientX - dragStart.x,
      y: event.clientY - dragStart.y,
    };
  };

  const handlePointerUp = () => {
    isDragging = false;
  };

  const renderCroppedBlob = async () => {
    if (!imagePreview) {
      return null;
    }
    const img = new Image();
    img.src = imagePreview;
    await img.decode();
    const size = 640;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    const baseScale = Math.max(size / img.width, size / img.height);
    const scale = baseScale * imageZoom;
    const drawWidth = img.width * scale;
    const drawHeight = img.height * scale;
    const dx = (size - drawWidth) / 2 + imageOffset.x;
    const dy = (size - drawHeight) / 2 + imageOffset.y;
    ctx.drawImage(img, dx, dy, drawWidth, drawHeight);
    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/jpeg", 0.9);
    });
  };

  const uploadCroppedImage = async () => {
    if (!adminId) {
      adminError = "Admin session missing.";
      return;
    }
    const blob = await renderCroppedBlob();
    if (!blob) {
      adminError = "Select an image first.";
      return;
    }
    const file = new File([blob], "drink.jpg", { type: "image/jpeg" });
    const response = await uploadImage(adminId, file);
    if (!response.ok) {
      adminError = response.data?.detail || "Image upload failed.";
      return;
    }
    adminForm = { ...adminForm, image_cover: `${API_BASE}${response.data.url}` };
  };

  const saveAdminDrink = async () => {
    adminError = "";
    if (!adminId) {
      adminError = "Admin session missing.";
      return;
    }
    if (!adminForm.name.trim()) {
      adminError = "Name is required.";
      return;
    }
    if (!adminForm.item_master_ids.length) {
      adminError = "Item master is required.";
      return;
    }
    const payload = {
      name: adminForm.name.trim(),
      description: adminForm.detail.trim().slice(0, 160),
      price: Number(adminForm.price) || 0,
      type: adminForm.type,
      image_cover: adminForm.image_cover.trim() || null,
      item_master_ids: adminForm.item_master_ids,
    };
    const response = adminEditingId
      ? await updateDrink(adminId, adminEditingId, payload)
      : await createDrink(adminId, payload);
    if (!response.ok) {
      adminError = response.data?.detail || "Save failed.";
      return;
    }
    await loadDrinks();
    resetAdminForm();
  };

  const editAdminDrink = (item) => {
    adminEditingId = item.id;
    adminForm = {
      name: item.name,
      detail: item.description || "",
      price: item.price,
      type: item.type || "other",
      item_master_ids: (item.item_masters || []).map((itemMaster) => itemMaster.id),
      image_cover: item.image_cover || "",
    };
    clearImage();
  };

  const deleteAdminDrink = async (id) => {
    if (!adminId) {
      adminError = "Admin session missing.";
      return;
    }
    const response = await deleteDrink(adminId, id);
    if (!response.ok) {
      adminError = response.data?.detail || "Delete failed.";
      return;
    }
    await loadDrinks();
    if (adminEditingId === id) {
      resetAdminForm();
    }
  };

  const saveItemMaster = async () => {
    adminError = "";
    if (!adminId) {
      adminError = "Admin session missing.";
      return;
    }
    if (!itemMasterForm.name.trim()) {
      adminError = "Item master name is required.";
      return;
    }
    const payload = {
      name: itemMasterForm.name.trim(),
    };
    const response = itemMasterEditingId
      ? await updateItemMaster(adminId, itemMasterEditingId, payload)
      : await createItemMaster(adminId, payload);
    if (!response.ok) {
      adminError = response.data?.detail || "Item master save failed.";
      return;
    }
    await loadItemMasters();
    resetItemMasterForm();
  };

  const editItemMaster = (itemMaster) => {
    itemMasterEditingId = itemMaster.id;
    itemMasterForm = {
      name: itemMaster.name,
    };
  };

  const deleteItemMaster = async (id) => {
    if (!adminId) {
      adminError = "Admin session missing.";
      return;
    }
    const response = await removeItemMaster(adminId, id);
    if (!response.ok) {
      adminError = response.data?.detail || "Item master delete failed.";
      return;
    }
    await loadItemMasters();
    if (itemMasterEditingId === id) {
      resetItemMasterForm();
    }
  };

  $: if (adminId && !hasLoaded) {
    hasLoaded = true;
    loadCatalog();
  }

  const formatPrice = (value) =>
    new Intl.NumberFormat("uz-UZ").format(value) + " UZS";
</script>

<div class="admin-workspace">
  <div class="admin-column">
    <form class="admin-form admin-card" on:submit|preventDefault={saveAdminDrink}>
    <div class="admin-card-head">
      <h2>{adminEditingId ? "Edit drink" : "Add new drink"}</h2>
    </div>
      <label>
        Drink name
        <input type="text" bind:value={adminForm.name} required />
      </label>
      <label>
        Description
        <textarea rows="3" maxlength="160" bind:value={adminForm.detail}></textarea>
        <span class="field-help">{adminForm.detail.length}/160</span>
      </label>
      <label>
        Price (UZS)
        <input type="number" min="0" step="500" bind:value={adminForm.price} />
      </label>
      <label>
        Item masters
        <select multiple size="6" bind:value={adminForm.item_master_ids}>
          {#each itemMasters as itemMaster}
            <option value={itemMaster.id}>{itemMaster.name}</option>
          {/each}
        </select>
      </label>
      <label>
        Image
        <div
          class="image-dropzone"
          on:drop={handleDrop}
          on:dragover={handleDragOver}
        >
          {#if imagePreview}
            <div
              class="image-preview"
              on:pointerdown={handlePointerDown}
              on:pointermove={handlePointerMove}
              on:pointerup={handlePointerUp}
              on:pointerleave={handlePointerUp}
            >
              <img
                src={imagePreview}
                alt="Preview"
                style={`transform: translate(${imageOffset.x}px, ${imageOffset.y}px) scale(${imageZoom});`}
                draggable="false"
              />
            </div>
          {:else}
            <div class="image-placeholder">
              <strong>Drag & drop an image</strong>
              <span>or click to browse</span>
            </div>
          {/if}
          <input class="image-input" type="file" accept="image/*" on:change={handleFileChange} />
        </div>
        {#if imagePreview}
          <div class="image-tools">
            <label>
              Zoom
              <input
                type="range"
                min="1"
                max="2"
                step="0.01"
                bind:value={imageZoom}
              />
            </label>
            <button type="button" class="ghost" on:click={clearImage}>
              Reset image
            </button>
            <button type="button" class="ghost" on:click={uploadCroppedImage}>
              Upload image
            </button>
          </div>
        {/if}
        {#if adminForm.image_cover}
          <div class="image-result">
            <img src={adminForm.image_cover} alt="Uploaded" />
            <span>Image ready for catalog.</span>
          </div>
        {/if}
      </label>
      <div class="admin-actions">
        <button type="submit" class="primary">
          {adminEditingId ? "Save changes" : "Add drink"}
        </button>
        {#if adminEditingId}
          <button type="button" class="ghost" on:click={resetAdminForm}>
            Cancel
          </button>
        {/if}
      </div>
      {#if adminError}
        <span class="admin-error">{adminError}</span>
      {/if}
    </form>

    <form class="admin-form admin-card" on:submit|preventDefault={saveItemMaster}>
      <div class="admin-card-head">
        <h2>{itemMasterEditingId ? "Edit item master" : "Add item master"}</h2>
      </div>
      <label>
        Item master name
        <input type="text" bind:value={itemMasterForm.name} required />
      </label>
      <div class="admin-actions">
        <button type="submit" class="primary">
          {itemMasterEditingId ? "Save changes" : "Add item master"}
        </button>
        {#if itemMasterEditingId}
          <button type="button" class="ghost" on:click={resetItemMasterForm}>
            Cancel
          </button>
        {/if}
      </div>
      {#if adminError}
        <span class="admin-error">{adminError}</span>
      {/if}
    </form>
  </div>

  <div class="admin-column admin-column-wide">
    <div class="admin-list admin-list-wide">
      {#each drinks as item}
        <div class="admin-item admin-item-wide">
          <div>
            <strong>{item.name}</strong>
            <span>{item.description}</span>
            <span class="admin-meta">
              {formatPrice(item.price)} - {(item.item_masters || []).map((itemMaster) => itemMaster.name).join(", ") || "Unassigned"}
            </span>
          </div>
          <div class="admin-item-actions">
            <button class="ghost" type="button" on:click={() => editAdminDrink(item)}>
              Edit
            </button>
            <button class="ghost danger" type="button" on:click={() => deleteAdminDrink(item.id)}>
              Remove
            </button>
          </div>
        </div>
      {/each}
    </div>

    <div class="admin-list admin-list-wide">
      {#each itemMasters as itemMaster}
        <div class="admin-item admin-item-wide">
          <div>
            <strong>{itemMaster.name}</strong>
            <span>Item master</span>
          </div>
          <div class="admin-item-actions">
            <button class="ghost" type="button" on:click={() => editItemMaster(itemMaster)}>
              Edit
            </button>
            <button class="ghost danger" type="button" on:click={() => deleteItemMaster(itemMaster.id)}>
              Remove
            </button>
          </div>
        </div>
      {/each}
    </div>
  </div>
</div>
