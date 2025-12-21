<script>
  import { onMount } from "svelte";

  let isAdmin = false;
  let pathLabel = "";
  let adminLoggedIn = false;
  let adminEmail = "";
  let adminPassword = "";
  let adminError = "";

  let catalog = [
    {
      id: 1,
      name: "MilkShake Classic",
      detail: "Vanilla bean, soft foam, slow melt.",
      price: 42000,
      category: "milkshake",
      image: "https://images.unsplash.com/photo-1521305916504-4a1121188589?auto=format&fit=crop&w=900&q=80",
    },
    {
      id: 2,
      name: "Cocoa Sprint",
      detail: "Dark chocolate, cold brew, sea salt.",
      price: 48000,
      category: "milkshake",
      image: "https://images.unsplash.com/photo-1511910849309-0dffb3b3a4f0?auto=format&fit=crop&w=900&q=80",
    },
    {
      id: 3,
      name: "Strawberry Glide",
      detail: "Fresh berry, oat base, light whip.",
      price: 46000,
      category: "milkshake",
      image: "https://images.unsplash.com/photo-1497534446932-c925b458314e?auto=format&fit=crop&w=900&q=80",
    },
    {
      id: 4,
      name: "Citrus Kick",
      detail: "Orange zest, lime mist, vanilla.",
      price: 39000,
      category: "soft",
      image: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=900&q=80",
    },
    {
      id: 5,
      name: "Matcha Flux",
      detail: "Ceremonial matcha, mint cloud.",
      price: 52000,
      category: "milkshake",
      image: "https://images.unsplash.com/photo-1517626597821-ef1f5b6f8d6b?auto=format&fit=crop&w=900&q=80",
    },
    {
      id: 6,
      name: "Honey Drift",
      detail: "Golden honey, toasted almond.",
      price: 45000,
      category: "soft",
      image: "https://images.unsplash.com/photo-1481671703460-040cb8a2d909?auto=format&fit=crop&w=900&q=80",
    },
  ];

  let cart = [];
  let lang = "en";
  let query = "";
  let activeCategory = "all";
  let orderMessage = "";
  let adminEditingId = null;
  let adminForm = {
    name: "",
    detail: "",
    price: 0,
    category: "milkshake",
    image: "",
  };
  let adminTab = "drinks";
  let adminOrders = [
    {
      id: "ORD-1001",
      name: "Amina",
      items: 3,
      total: 126000,
      status: "pending",
      time: "2 min ago",
    },
    {
      id: "ORD-1002",
      name: "Bek",
      items: 2,
      total: 94000,
      status: "in_progress",
      time: "8 min ago",
    },
    {
      id: "ORD-1003",
      name: "Camila",
      items: 1,
      total: 52000,
      status: "ready",
      time: "12 min ago",
    },
  ];

  const categories = ["all", "milkshake", "cola", "water", "soft", "alcohol"];
  const adminCategories = ["milkshake", "cola", "water", "soft", "alcohol"];
  const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

  const copy = {
    en: {
      brandTag: "QR-driven ordering",
      search: "Search drinks...",
      eyebrow: "Milkshake Ordering",
      heroTitle: "Pick a drink. Add to order. Done.",
      heroBody:
        "A clean menu for ordering milkshakes. Photos, prices, and a quick cart — nothing else.",
      featured: "Featured",
      catalogTitle: "Milkshake catalog",
      catalogBody: "Pick a drink, see the photo, and add it to your order.",
      orderTitle: "Order summary",
      orderBody: "Review your selections before checkout.",
      emptyTitle: "No drinks selected yet.",
      emptyBody: "Tap any milkshake to add it to your order.",
      aboutTitle: "About",
      aboutBody:
        "MilkShake is a QR-driven drink ordering web app. Guests scan and order instantly, admins control the menu, and staff run a live order queue.",
      addToOrder: "Add to order",
      subtotal: "Subtotal",
      placeOrder: "Place order",
      orderPlaced: "Order placed! We'll start preparing your drinks.",
      noResultsTitle: "No drinks found.",
      noResultsBody: "Try a different search or category.",
      adminAccess: "Admin access at /admin (direct URL)",
      categories: {
        all: "All",
        milkshake: "Milkshake",
        cola: "Cola",
        water: "Water",
        soft: "Soft drink",
        alcohol: "Alcoholic",
      },
      language: "Language",
    },
    ru: {
      brandTag: "QR-заказ напитков",
      search: "Поиск напитков...",
      eyebrow: "Заказ милкшейков",
      heroTitle: "Выберите напиток. Добавьте. Готово.",
      heroBody:
        "Чистое меню для заказа милкшейков. Фото, цены и быстрый заказ — ничего лишнего.",
      featured: "Рекомендуем",
      catalogTitle: "Каталог милкшейков",
      catalogBody: "Выберите напиток, посмотрите фото и добавьте в заказ.",
      orderTitle: "Ваш заказ",
      orderBody: "Проверьте позиции перед оформлением.",
      emptyTitle: "Пока нет выбранных напитков.",
      emptyBody: "Нажмите на милкшейк, чтобы добавить его в заказ.",
      aboutTitle: "О проекте",
      aboutBody:
        "MilkShake — это веб‑приложение для заказа напитков по QR. Гости сканируют код и заказывают, администраторы управляют меню, а персонал работает с очередью.",
      addToOrder: "В заказ",
      subtotal: "Итого",
      placeOrder: "Оформить заказ",
      orderPlaced: "Заказ оформлен! Мы начинаем готовить напитки.",
      noResultsTitle: "Ничего не найдено.",
      noResultsBody: "Попробуйте другой поиск или категорию.",
      adminAccess: "Админ доступ: /admin (прямой URL)",
      categories: {
        all: "Все",
        milkshake: "Милкшейк",
        cola: "Кола",
        water: "Вода",
        soft: "Безалкогольные",
        alcohol: "Алкогольные",
      },
      language: "Язык",
    },
    uz: {
      brandTag: "QR orqali buyurtma",
      search: "Ichimlik qidirish...",
      eyebrow: "Milkshake buyurtma",
      heroTitle: "Ichimlik tanlang. Buyurtma qiling. Tayyor.",
      heroBody:
        "Milkshake buyurtma berish uchun sodda menyu. Rasm, narx va tezkor savat — xolos.",
      featured: "Tavsiya",
      catalogTitle: "Milkshake katalogi",
      catalogBody: "Ichimlikni tanlang, rasmni ko‘ring va buyurtmaga qo‘shing.",
      orderTitle: "Buyurtma",
      orderBody: "Buyurtmani yakunlashdan oldin tekshiring.",
      emptyTitle: "Hozircha ichimlik tanlanmagan.",
      emptyBody: "Buyurtmaga qo‘shish uchun milkshake ustiga bosing.",
      aboutTitle: "Loyiha haqida",
      aboutBody:
        "MilkShake — QR orqali ichimlik buyurtma berish veb‑ilovasi. Mehmonlar skanerlab buyurtma qiladi, adminlar menyuni boshqaradi, xodimlar esa navbat bilan ishlaydi.",
      addToOrder: "Buyurtmaga qo‘shish",
      subtotal: "Jami",
      placeOrder: "Buyurtma berish",
      orderPlaced: "Buyurtma qabul qilindi! Ichimliklar tayyorlanmoqda.",
      noResultsTitle: "Ichimlik topilmadi.",
      noResultsBody: "Qidiruv yoki kategoriya ni o‘zgartiring.",
      adminAccess: "Admin kirish: /admin (to‘g‘ridan‑to‘g‘ri URL)",
      categories: {
        all: "Barchasi",
        milkshake: "Milkshake",
        cola: "Kola",
        water: "Suv",
        soft: "Gazsiz ichimlik",
        alcohol: "Spirtli",
      },
      language: "Til",
    },
  };

  const formatPrice = (value) =>
    new Intl.NumberFormat("uz-UZ").format(value) + " UZS";

  const addToCart = (item) => {
    const existing = cart.find((entry) => entry.id === item.id);
    if (existing) {
      cart = cart.map((entry) =>
        entry.id === item.id ? { ...entry, qty: entry.qty + 1 } : entry
      );
      orderMessage = "";
      return;
    }
    cart = [...cart, { ...item, qty: 1 }];
    orderMessage = "";
  };

  const updateQty = (id, delta) => {
    cart = cart
      .map((entry) =>
        entry.id === id ? { ...entry, qty: Math.max(0, entry.qty + delta) } : entry
      )
      .filter((entry) => entry.qty > 0);
    orderMessage = "";
  };

  $: subtotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0);
  $: filteredCatalog = catalog.filter((item) => {
    const matchesCategory =
      activeCategory === "all" ? true : item.category === activeCategory;
    const matchesQuery = `${item.name} ${item.detail}`
      .toLowerCase()
      .includes(query.trim().toLowerCase());
    return matchesCategory && matchesQuery;
  });

  const placeOrder = () => {
    if (cart.length === 0) {
      orderMessage = copy[lang].emptyTitle;
      return;
    }
    orderMessage = copy[lang].orderPlaced;
    cart = [];
  };

  const loginAdmin = async () => {
    adminError = "";
    try {
      const response = await fetch(`${API_BASE}/api/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: adminEmail.trim().toLowerCase(),
          password: adminPassword,
        }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        adminError = data?.detail || "Login failed.";
        return;
      }
      adminLoggedIn = true;
      adminPassword = "";
    } catch (error) {
      adminError = "Login failed.";
    }
  };

  const resetAdminForm = () => {
    adminForm = {
      name: "",
      detail: "",
      price: 0,
      category: "milkshake",
      image: "",
    };
    adminEditingId = null;
  };

  const saveAdminDrink = () => {
    if (!adminForm.name.trim()) {
      adminError = "Name is required.";
      return;
    }
    const payload = {
      ...adminForm,
      price: Number(adminForm.price) || 0,
      name: adminForm.name.trim(),
      detail: adminForm.detail.trim(),
      image: adminForm.image.trim(),
    };
    if (adminEditingId) {
      const idx = catalog.findIndex((item) => item.id === adminEditingId);
      if (idx >= 0) {
        catalog[idx] = { ...catalog[idx], ...payload };
        catalog = [...catalog];
      }
    } else {
      const nextId = Math.max(0, ...catalog.map((item) => item.id)) + 1;
      catalog = [...catalog, { ...payload, id: nextId }];
    }
    adminError = "";
    resetAdminForm();
  };

  const editAdminDrink = (item) => {
    adminEditingId = item.id;
    adminForm = {
      name: item.name,
      detail: item.detail,
      price: item.price,
      category: item.category,
      image: item.image,
    };
  };

  const deleteAdminDrink = (id) => {
    catalog = catalog.filter((item) => item.id !== id);
    if (adminEditingId === id) {
      resetAdminForm();
    }
  };

  onMount(() => {
    const path = window.location.pathname;
    isAdmin = path.startsWith("/admin");
    pathLabel = path;
  });
</script>

{#if isAdmin}
  <div class="admin-shell">
    <header class="admin-header">
      <span class="brand">MilkShake Admin</span>
      <span class="path">Path: {pathLabel}</span>
    </header>
    {#if !adminLoggedIn}
      <section class="admin-panel">
        <h1>Secure sign-in</h1>
        <p>Enter your admin credentials to continue.</p>
        <form
          class="admin-form"
          on:submit|preventDefault={loginAdmin}
        >
          <label>
            Email
            <input
              type="email"
              placeholder="admin@milkshake.local"
              bind:value={adminEmail}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              placeholder="••••••••"
              bind:value={adminPassword}
              required
            />
          </label>
          <button type="submit">Sign in</button>
        </form>
        {#if adminError}
          <span class="admin-error">{adminError}</span>
        {/if}
        <span class="admin-note">
          Admin login is managed in Postgres.
        </span>
      </section>
    {:else}
      <section class="admin-panel admin-dashboard">
        <div class="admin-top">
          <div>
            <h1>MilkShake Admin Desk</h1>
            <p>Manage drinks, categories, and monitor incoming orders.</p>
          </div>
          <div class="admin-tabs">
            <button
              type="button"
              class={`pill ${adminTab === "drinks" ? "is-active" : ""}`}
              on:click={() => (adminTab = "drinks")}
            >
              Drinks
            </button>
            <button
              type="button"
              class={`pill ${adminTab === "orders" ? "is-active" : ""}`}
              on:click={() => (adminTab = "orders")}
            >
              Orders
            </button>
          </div>
        </div>

        {#if adminTab === "drinks"}
          <div class="admin-grid">
            <form
              class="admin-form admin-editor"
              on:submit|preventDefault={saveAdminDrink}
            >
              <div class="admin-editor-head">
                <h2>{adminEditingId ? "Edit drink" : "Add new drink"}</h2>
                <button class="ghost" type="button" on:click={resetAdminForm}>
                  New drink
                </button>
              </div>
              <label>
                Drink name
                <input type="text" bind:value={adminForm.name} required />
              </label>
              <label>
                Description
                <textarea rows="3" bind:value={adminForm.detail}></textarea>
              </label>
              <label>
                Price (UZS)
                <input type="number" min="0" step="500" bind:value={adminForm.price} />
              </label>
              <label>
                Category
                <select bind:value={adminForm.category}>
                  {#each adminCategories as category}
                    <option value={category}>{category}</option>
                  {/each}
                </select>
              </label>
              <label>
                Image URL
                <input type="url" bind:value={adminForm.image} />
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
            <div class="admin-list">
              {#each catalog as item}
                <div class="admin-item">
                  <div class="admin-thumb">
                    {#if item.image}
                      <img src={item.image} alt={item.name} />
                    {:else}
                      <span>IMG</span>
                    {/if}
                  </div>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.detail}</span>
                    <span class="admin-meta">
                      {formatPrice(item.price)} · {item.category}
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
          </div>
        {:else}
          <div class="admin-orders">
            <div class="admin-orders-head">
              <h2>Incoming orders</h2>
              <span>Live queue overview</span>
            </div>
            <div class="admin-orders-grid">
              {#each adminOrders as order}
                <div class={`admin-order-card status-${order.status}`}>
                  <div>
                    <strong>{order.id}</strong>
                    <span>{order.name} · {order.items} items</span>
                  </div>
                  <div class="admin-order-meta">
                    <span>{formatPrice(order.total)}</span>
                    <span>{order.time}</span>
                  </div>
                  <div class="admin-order-actions">
                    <button class="ghost" type="button">Mark ready</button>
                    <button class="ghost danger" type="button">Cancel</button>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </section>
    {/if}
  </div>
{:else}
  <div class="page">
    <header class="topbar sticky">
      <div class="brand-block">
        <span class="logo"></span>
        <div>
          <span class="brand">MilkShake</span>
          <span class="tag">QR-driven ordering</span>
        </div>
      </div>
      <div class="topbar-actions">
        <div class="search">
          <input
            type="search"
            placeholder={copy[lang].search}
            aria-label={copy[lang].search}
            bind:value={query}
          />
        </div>
        <div class="lang-switch">
          <span>{copy[lang].language}</span>
          <button
            class:active={lang === "en"}
            on:click={() => (lang = "en")}
            type="button"
          >
            ENG
          </button>
          <button
            class:active={lang === "ru"}
            on:click={() => (lang = "ru")}
            type="button"
          >
            RUS
          </button>
          <button
            class:active={lang === "uz"}
            on:click={() => (lang = "uz")}
            type="button"
          >
            UZB
          </button>
        </div>
      </div>
    </header>

    <main>
      <section class="hero">
        <div class="hero-copy">
          <span class="eyebrow">{copy[lang].eyebrow}</span>
          <h1>{copy[lang].heroTitle}</h1>
          <p>
            {copy[lang].heroBody}
          </p>
        </div>
        <div class="hero-card">
          <div class="card-top">
            <span class="chip">{copy[lang].featured}</span>
            <span class="price">{formatPrice(catalog[0].price)}</span>
          </div>
          <h3>{catalog[0].name}</h3>
          <p>{catalog[0].detail}</p>
          <div class="card-actions">
            <button on:click={() => addToCart(catalog[0])}>
              {copy[lang].addToOrder}
            </button>
          </div>
        </div>
      </section>

      <section class="section" id="catalog">
        <div class="section-head">
          <h2>{copy[lang].catalogTitle}</h2>
          <p>{copy[lang].catalogBody}</p>
        </div>
        <div class="category-row">
          {#each categories as category}
            <button
              type="button"
              class={`pill ${activeCategory === category ? "is-active" : ""}`}
              on:click={() => (activeCategory = category)}
            >
              {copy[lang].categories[category]}
            </button>
          {/each}
        </div>
        <div class="grid catalog-grid">
          {#if filteredCatalog.length === 0}
            <div class="empty-list">
              <span>{copy[lang].noResultsTitle}</span>
              <span>{copy[lang].noResultsBody}</span>
            </div>
          {:else}
            {#each filteredCatalog as item, index}
            <article class="tile reveal catalog-card" style={`--d:${index * 80}ms`}>
              <div class="catalog-image">
                <img src={item.image} alt={item.name} loading="lazy" />
              </div>
              <div class="catalog-body">
                <div class="catalog-top">
                  <h3>{item.name}</h3>
                  <span class="catalog-price">{formatPrice(item.price)}</span>
                </div>
                <span>{item.detail}</span>
                <button on:click={() => addToCart(item)}>
                  {copy[lang].addToOrder}
                </button>
              </div>
            </article>
            {/each}
          {/if}
        </div>
      </section>

      <section class="section" id="order">
        <div class="section-head">
          <h2>{copy[lang].orderTitle}</h2>
          <p>{copy[lang].orderBody}</p>
        </div>
        <div class="cart">
          {#if cart.length === 0}
            <div class="empty">
              <span>{copy[lang].emptyTitle}</span>
              <span>{copy[lang].emptyBody}</span>
            </div>
          {:else}
            {#each cart as item}
              <div class="cart-row">
                <div>
                  <strong>{item.name}</strong>
                  <span>{formatPrice(item.price)}</span>
                </div>
                <div class="qty">
                  <button class="ghost" on:click={() => updateQty(item.id, -1)}>-</button>
                  <span>{item.qty}</span>
                  <button class="ghost" on:click={() => updateQty(item.id, 1)}>+</button>
                </div>
                <span class="line-total">{formatPrice(item.price * item.qty)}</span>
              </div>
            {/each}
            <div class="cart-total">
              <span>{copy[lang].subtotal}</span>
              <strong>{formatPrice(subtotal)}</strong>
            </div>
            <button class="primary checkout" on:click={placeOrder}>
              {copy[lang].placeOrder}
            </button>
          {/if}
          {#if orderMessage}
            <div class="order-message">{orderMessage}</div>
          {/if}
        </div>
      </section>

      <section class="section" id="about">
        <div class="section-head">
          <h2>{copy[lang].aboutTitle}</h2>
          <p>{copy[lang].aboutBody}</p>
        </div>
      </section>
    </main>

    <footer class="footer">
      <span>MilkShake UI • Svelte + Vite</span>
      <span>{copy[lang].adminAccess}</span>
    </footer>
  </div>
{/if}
