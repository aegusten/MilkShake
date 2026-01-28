<script>
  import { onMount } from "svelte";
  import { fetchItemMasters, fetchDrinks, createOrder } from "../../api/index.js";

  let drinks = [];
  let itemMasters = [];
  let cart = [];
  let lang = "en";
  let query = "";
  let activeItemMaster = "all";
  let orderMessage = "";
  let orderError = "";
  let orderLoading = false;
  let guestName = "";
  let guestPhone = "";

  const copy = {
    en: {
      brandTag: "QR-driven ordering",
      search: "Search drinks...",
      eyebrow: "Milkshake Ordering",
      heroTitle: "Pick a drink. Add to order. Done.",
      heroBody:
        "A clean menu for ordering milkshakes. Photos, prices, and a quick cart - nothing else.",
      featured: "Featured",
      catalogTitle: "Milkshake catalog",
      catalogBody: "Pick a drink, see the photo, and add it to your order.",
      orderTitle: "Order summary",
      orderBody: "Review your selections before checkout.",
      guestName: "Guest name",
      guestPhone: "Phone (optional)",
      guestNamePlaceholder: "Enter your name",
      guestPhonePlaceholder: "+998 00 000 00 00",
      emptyTitle: "No drinks selected yet.",
      emptyBody: "Tap any milkshake to add it to your order.",
      aboutTitle: "About",
      aboutBody:
        "MilkShake is a QR-driven drink ordering web app. Guests scan and order instantly, admins control the menu, and staff run a live order queue.",
      addToOrder: "Add to order",
      subtotal: "Subtotal",
      placeOrder: "Place order",
      sending: "Sending...",
      orderPlaced: "Order placed! We'll start preparing your drinks.",
      orderFailed: "Order failed. Please try again.",
      nameRequired: "Please enter your name.",
      noResultsTitle: "No drinks found.",
      noResultsBody: "Try a different search or item master.",
      adminAccess: "Admin access at /admin (direct URL)",
      itemMasters: {
        all: "All",
      },
      language: "Language",
    },
    ru: {
      brandTag: "????? ????? QR",
      search: "????? ????????...",
      eyebrow: "????? MilkShake",
      heroTitle: "???????? ???????. ???????? ? ?????. ??????.",
      heroBody:
        "?????? ???? ??? ?????? ??????????. ????, ???? ? ??????? ????? - ?????? ???????.",
      featured: "?????????",
      catalogTitle: "??????? MilkShake",
      catalogBody: "???????? ???????, ?????????? ???? ? ???????? ? ?????.",
      orderTitle: "?????",
      orderBody: "????????? ????? ????? ???????????.",
      guestName: "??? ?????",
      guestPhone: "????? (?? ??????)",
      guestNamePlaceholder: "??? ???",
      guestPhonePlaceholder: "+998 00 000 00 00",
      emptyTitle: "???? ?????? ?? ???????.",
      emptyBody: "??????? ?? ????????, ????? ???????? ? ?????.",
      aboutTitle: "? ???????",
      aboutBody:
        "MilkShake - ???-?????????? ??? ?????? ???????? ?? QR. ????? ????????? ? ??????????, ?????? ????????? ????, ?????????? ????? ???????.",
      addToOrder: "???????? ? ?????",
      subtotal: "?????",
      placeOrder: "???????? ?????",
      sending: "?????????...",
      orderPlaced: "????? ??????! ?? ???????? ???????? ???????.",
      orderFailed: "????? ?? ???????. ?????????? ????.",
      nameRequired: "????????? ??? ???.",
      noResultsTitle: "??????? ?? ???????.",
      noResultsBody: "?????????? ?????? ????? ??? ???????????.",
      adminAccess: "???? ??? ??????: /admin (?????? ??????)",
      itemMasters: {
        all: "???",
      },
      language: "????",
    },
    uz: {
      brandTag: "QR orqali buyurtma",
      search: "Ichimlik qidirish...",
      eyebrow: "MilkShake buyurtma",
      heroTitle: "Ichimlik tanlang. Buyurtma qiling. Tayyor.",
      heroBody:
        "Milkshake buyurtma berish uchun sodda menyu. Rasmlar, narxlar va tezkor savat - xolos.",
      featured: "Tavsiya",
      catalogTitle: "MilkShake katalogi",
      catalogBody: "Ichimlikni tanlang, rasmini ko'ring va buyurtmaga qo'shing.",
      orderTitle: "Buyurtma",
      orderBody: "Buyurtmani yakunlashdan oldin tekshiring.",
      guestName: "Mehmon ismi",
      guestPhone: "Telefon (ixtiyoriy)",
      guestNamePlaceholder: "Ismingizni kiriting",
      guestPhonePlaceholder: "+998 00 000 00 00",
      emptyTitle: "Hozircha ichimlik tanlanmagan.",
      emptyBody: "Buyurtmaga qo'shish uchun milkshake ustiga bosing.",
      aboutTitle: "Loyiha haqida",
      aboutBody:
        "MilkShake - QR orqali ichimlik buyurtma berish veb-ilovasi. Mehmonlar skanerlab buyurtma qiladi, adminlar menyuni boshqaradi, xodimlar esa navbat bilan ishlaydi.",
      addToOrder: "Buyurtmaga qo'shish",
      subtotal: "Jami",
      placeOrder: "Buyurtma berish",
      sending: "Yuborilmoqda...",
      orderPlaced: "Buyurtma qabul qilindi! Ichimliklar tayyorlanmoqda.",
      orderFailed: "Buyurtma yuborilmadi. Qayta urinib ko'ring.",
      nameRequired: "Ismingizni kiriting.",
      noResultsTitle: "Ichimlik topilmadi.",
      noResultsBody: "Qidiruv yoki yo'nalishni o'zgartiring.",
      adminAccess: "Admin kirish: /admin (to'g'ridan-to'g'ri URL)",
      itemMasters: {
        all: "Barchasi",
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
  $: featuredDrink = drinks[0];
  $: filteredCatalog = drinks.filter((item) => {
    const matchesQuery = `${item.name} ${item.description || ""}`
      .toLowerCase()
      .includes(query.trim().toLowerCase());
    if (activeItemMaster === "all") {
      return matchesQuery;
    }
    return (
      matchesQuery &&
      (item.item_masters || []).some((itemMaster) => itemMaster.id === activeItemMaster)
    );
  });

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

  const placeOrder = () => {
    orderError = "";
    if (cart.length === 0) {
      orderMessage = copy[lang].emptyTitle;
      return;
    }
    if (!guestName.trim()) {
      orderMessage = copy[lang].nameRequired;
      return;
    }
    orderLoading = true;
    createOrder({
      guest_name: guestName.trim(),
      phone: guestPhone.trim() || null,
      items: cart.map((item) => ({
        drink_id: item.id,
        quantity: item.qty,
      })),
    })
      .then((response) => {
        if (!response.ok) {
          orderError = response.data?.detail || copy[lang].orderFailed;
          return;
        }
        orderMessage = copy[lang].orderPlaced;
        cart = [];
        guestName = "";
        guestPhone = "";
      })
      .catch(() => {
        orderError = copy[lang].orderFailed;
      })
      .finally(() => {
        orderLoading = false;
      });
  };

  const selectItemMaster = (id) => {
    activeItemMaster = id;
  };

  onMount(() => {
    loadCatalog();
  });
</script>

<div class="page">
  <header class="topbar sticky">
    <div class="brand-block">
      <span class="logo"></span>
      <div>
        <span class="brand">MilkShake</span>
        <span class="tag">{copy[lang].brandTag}</span>
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
        <p>{copy[lang].heroBody}</p>
      </div>
      <div class="hero-card">
        {#if featuredDrink}
          <div class="card-top">
            <span class="chip">{copy[lang].featured}</span>
            <span class="price">{formatPrice(featuredDrink.price)}</span>
          </div>
          <h3>{featuredDrink.name}</h3>
          <p>{featuredDrink.description}</p>
          <div class="card-actions">
            <button on:click={() => addToCart(featuredDrink)}>
              {copy[lang].addToOrder}
            </button>
          </div>
        {:else}
          <div class="card-top">
            <span class="chip">{copy[lang].featured}</span>
          </div>
          <h3>{copy[lang].noResultsTitle}</h3>
          <p>{copy[lang].noResultsBody}</p>
        {/if}
      </div>
    </section>

    <section class="section" id="catalog">
      <div class="section-head">
        <h2>{copy[lang].catalogTitle}</h2>
        <p>{copy[lang].catalogBody}</p>
      </div>
      <div class="category-row">
        <button
          type="button"
          class={`pill ${activeItemMaster === "all" ? "is-active" : ""}`}
          on:click={() => selectItemMaster("all")}
        >
          {copy[lang].itemMasters.all}
        </button>
        {#each itemMasters as itemMaster}
          <button
            type="button"
            class={`pill ${activeItemMaster === itemMaster.id ? "is-active" : ""}`}
            on:click={() => selectItemMaster(itemMaster.id)}
          >
            {itemMaster.name}
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
                <img
                  src={item.image_cover || "https://images.unsplash.com/photo-1481671703460-040cb8a2d909?auto=format&fit=crop&w=900&q=80"}
                  alt={item.name}
                  loading="lazy"
                />
              </div>
              <div class="catalog-body">
                <div class="catalog-top">
                  <h3>{item.name}</h3>
                  <span class="catalog-price">{formatPrice(item.price)}</span>
                </div>
                <span>{item.description}</span>
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
        <div class="order-fields">
          <label>
            {copy[lang].guestName}
            <input
              type="text"
              placeholder={copy[lang].guestNamePlaceholder}
              bind:value={guestName}
              required
            />
          </label>
          <label>
            {copy[lang].guestPhone}
            <input
              type="tel"
              placeholder={copy[lang].guestPhonePlaceholder}
              bind:value={guestPhone}
            />
          </label>
        </div>
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
          <button class="primary checkout" on:click={placeOrder} disabled={orderLoading}>
            {orderLoading ? copy[lang].sending : copy[lang].placeOrder}
          </button>
        {/if}
        {#if orderError}
          <div class="order-message">{orderError}</div>
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
    <span>MilkShake UI - Svelte + Vite</span>
    <span>{copy[lang].adminAccess}</span>
  </footer>
</div>
