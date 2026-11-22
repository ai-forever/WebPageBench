(function () {
  var TARGET = "item_150030882";
  var theme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  var taskId = theme === "dark"
    ? "ecommerce_basket_named_product_02__theme_dark"
    : "ecommerce_basket_named_product_02";
  var themeLabel = theme === "dark" ? "Тёмная тема" : "Светлая тема";
  var homeHref = document.body.getAttribute("data-home") || "../";
  var otherHref = document.body.getAttribute("data-other") || (theme === "dark" ? "../light/" : "../dark/");
  var otherLabel = document.body.getAttribute("data-other-label") || (theme === "dark" ? "Светлая тема" : "Тёмная тема");

  var PRODUCTS = [
    {
      id: "item_136495278",
      brand: "Whiskas",
      name: "Whiskas для стерилизованных кошек, с курицей, 5 кг",
      price: 1668,
      rating: "4.9",
      reviews: "93\u202f757",
      hue: "#e0a106"
    },
    {
      id: "item_150030882",
      brand: "Purina ONE",
      name: "Purina ONE для стерилизованных кошек, с говядиной и пшеницей, 3 кг",
      price: 1297,
      rating: "5.0",
      reviews: "576\u202f145",
      hue: "#c46a2f"
    },
    {
      id: "item_140701758",
      brand: "Purina ONE",
      name: "Purina ONE для домашних кошек, с индейкой и злаками, 3 кг",
      price: 4429,
      rating: "5.0",
      reviews: "183\u202f142",
      hue: "#8d6a45"
    },
    {
      id: "item_1805895777",
      brand: "CATTERA",
      name: "CATTERA для взрослых кошек, с говядиной, 3×300 г",
      price: 1544,
      rating: "4.9",
      reviews: "8\u202f104",
      hue: "#6d8f52"
    },
    {
      id: "item_2316709053",
      brand: "PERFECT FIT",
      name: "PERFECT FIT, сухой корм с лососем для взрослых кошек, 1,2 кг",
      price: 1100,
      rating: "4.9",
      reviews: "609",
      hue: "#d07a6a"
    },
    {
      id: "item_387906561",
      brand: "Whiskas",
      name: "Whiskas, влажный корм, набор желе и мясная коллекция",
      price: 1050,
      rating: "5.0",
      reviews: "99\u202f942",
      hue: "#7b6b9a"
    },
    {
      id: "item_2316708961",
      brand: "PERFECT FIT",
      name: "PERFECT FIT, влажный корм для котят, говядина в соусе, 28×75 г",
      price: 1100,
      rating: "4.9",
      reviews: "336",
      hue: "#5d84ad"
    },
    {
      id: "item_1117085974",
      brand: "KIX",
      name: "KIX, туалетная бумага, сандал и ягоды, 12 рулонов",
      price: 2223,
      rating: "4.9",
      reviews: "230\u202f371",
      hue: "#8aa0b8"
    }
  ];

  var byId = {};
  PRODUCTS.forEach(function (product) { byId[product.id] = product; });

  var state = load() || { query: "", view: "catalog", cart: {}, log: [] };

  var app = document.getElementById("app");
  app.innerHTML =
    '<div class="chrome">' +
      '<div class="topbar">' +
        '<span>WebPageBench · демо · ' + esc(themeLabel) + '</span>' +
        '<nav>' +
          '<a href="' + esc(otherHref) + '">' + esc(otherLabel) + '</a>' +
          '<a href="' + esc(homeHref) + '">Оба варианта</a>' +
        '</nav>' +
      '</div>' +
      '<header class="market-header">' +
        '<button type="button" class="wordmark" data-action="home">Маркет</button>' +
        '<form class="search" id="search-form" role="search">' +
          '<label class="sr" for="q">Поиск по товарам</label>' +
          '<input id="q" type="search" placeholder="Искать на Маркете" autocomplete="off" />' +
          '<button type="submit">Найти</button>' +
        '</form>' +
        '<button type="button" class="cart-btn" data-action="cart" id="cart-btn">' +
          bagIcon() +
          '<span>Корзина</span>' +
          '<span class="badge" id="badge" hidden>0</span>' +
        '</button>' +
      '</header>' +
    '</div>' +
    '<main class="wrap">' +
      '<section class="task">' +
        '<p class="task-kicker">' + esc(taskId) + '</p>' +
        '<p class="task-text">В «Маркете» найдите сухой корм Purina ONE для стерилизованных кошек с говядиной и пшеницей и добавьте в корзину.</p>' +
        '<p class="task-status" id="status"></p>' +
      '</section>' +
      '<section class="panel" id="panel"></section>' +
      '<section class="log">' +
        '<h2>События страницы</h2>' +
        '<p>Задание сверяется с последним событием по этому товару: <span class="mono">basket_add</span>, <span class="mono">item_150030882</span>, <span class="mono">amount 1</span>.</p>' +
        '<ol id="log"></ol>' +
      '</section>' +
    '</main>';

  var queryInput = document.getElementById("q");
  queryInput.value = state.query;
  queryInput.addEventListener("input", function () {
    state.query = queryInput.value;
    state.view = "catalog";
    save();
    paint();
  });
  document.getElementById("search-form").addEventListener("submit", function (event) {
    event.preventDefault();
    state.view = "catalog";
    save();
    paint();
  });
  app.addEventListener("click", function (event) {
    var el = event.target.closest("[data-action]");
    if (!el || !app.contains(el)) return;
    var action = el.getAttribute("data-action");
    var id = el.getAttribute("data-id");
    if (action === "add" || action === "inc") change(id, 1);
    else if (action === "dec") change(id, -1);
    else if (action === "remove") removeItem(id);
    else if (action === "cart") {
      state.view = "cart";
      save();
      paint();
    } else if (action === "catalog") {
      state.view = "catalog";
      save();
      paint();
    } else if (action === "home") {
      state.view = "catalog";
      state.query = "";
      queryInput.value = "";
      save();
      paint();
    }
  });

  paint();

  function change(id, delta) {
    if (!byId[id]) return;
    var next = Math.max(0, (state.cart[id] || 0) + delta);
    if (next === 0) delete state.cart[id];
    else state.cart[id] = next;
    pushLog(delta > 0 ? "basket_add" : "basket_remove", id, next);
  }

  function removeItem(id) {
    if (!state.cart[id]) return;
    delete state.cart[id];
    pushLog("basket_remove", id, 0);
  }

  function pushLog(type, id, amount) {
    state.log.unshift({ type: type, item_id: id, amount: amount });
    if (state.log.length > 8) state.log.length = 8;
    save();
    paint();
  }

  function paint() {
    var count = Object.keys(state.cart).reduce(function (sum, id) {
      return sum + state.cart[id];
    }, 0);
    var badge = document.getElementById("badge");
    badge.hidden = count === 0;
    badge.textContent = String(count);
    document.getElementById("cart-btn").setAttribute(
      "aria-label",
      count ? "Корзина, товаров: " + count : "Корзина пуста"
    );

    var qty = state.cart[TARGET] || 0;
    var status = document.getElementById("status");
    status.className = "task-status";
    if (qty === 1) {
      status.classList.add("ok");
      status.textContent = "В корзине одна упаковка нужного корма. Для этого задания этого достаточно.";
    } else if (qty > 1) {
      status.classList.add("warn");
      status.textContent = "В корзине несколько упаковок. Задание ждёт одну.";
    } else {
      status.textContent = "Нужного корма в корзине ещё нет.";
    }

    document.getElementById("panel").innerHTML = state.view === "cart" ? cartHtml() : catalogHtml();

    var log = document.getElementById("log");
    if (!state.log.length) {
      log.innerHTML = "<li>Пока пусто.</li>";
    } else {
      log.innerHTML = state.log.map(function (entry) {
        return "<li>" + esc(entry.type + "   " + entry.item_id + "   amount " + entry.amount) + "</li>";
      }).join("");
    }
  }

  function catalogHtml() {
    var visible = PRODUCTS.filter(function (product) {
      return matches(product, state.query);
    });
    var title = state.query.trim() ? "Результаты поиска" : "Товары";
    var body = visible.length
      ? '<div class="cards">' + visible.map(cardHtml).join("") + '</div>'
      : '<p class="empty">Ничего не найдено. Сбросьте запрос или откройте всю витрину.</p>';
    return (
      '<div class="panel-head"><h2>' + esc(title) + '</h2><p>' + visible.length + ' из ' + PRODUCTS.length + '</p></div>' +
      body
    );
  }

  function cardHtml(product) {
    var qty = state.cart[product.id] || 0;
    var control = qty > 0
      ? '<div class="stepper">' +
          '<button type="button" data-action="dec" data-id="' + esc(product.id) + '" aria-label="Убрать одну">−</button>' +
          '<span>' + qty + '</span>' +
          '<button type="button" data-action="inc" data-id="' + esc(product.id) + '" aria-label="Добавить ещё">+</button>' +
        '</div>'
      : '<button type="button" class="add" data-action="add" data-id="' + esc(product.id) + '">В корзину</button>';
    return (
      '<article class="card" data-item-id="' + esc(product.id) + '">' +
        '<div class="thumb" style="--hue:' + esc(product.hue) + '">' + bagIcon() + '<span class="brand-tag">' + esc(product.brand) + '</span></div>' +
        '<div class="price-row">' +
          '<span class="price">' + esc(money(product.price)) + '</span>' +
          '<span class="old">' + esc(money(Math.round(product.price / 0.9))) + '</span>' +
          '<span class="disc">−10%</span>' +
        '</div>' +
        '<p class="name">' + esc(product.name) + '</p>' +
        '<div class="meta"><b>' + esc(product.rating) + '</b> · ' + esc(product.reviews) + '</div>' +
        control +
      '</article>'
    );
  }

  function cartHtml() {
    var ids = Object.keys(state.cart);
    if (!ids.length) {
      return (
        '<div class="panel-head"><h2>Корзина</h2></div>' +
        '<p class="empty">В корзине пока пусто.</p>' +
        '<p><button type="button" class="text-btn" data-action="catalog">К товарам</button></p>'
      );
    }
    var total = 0;
    var lines = ids.map(function (id) {
      var product = byId[id];
      var qty = state.cart[id];
      total += product.price * qty;
      return (
        '<div class="cart-line">' +
          '<div class="cart-thumb" style="--hue:' + esc(product.hue) + '">' + bagIcon() + '</div>' +
          '<div>' +
            '<p class="cart-name">' + esc(product.name) + '</p>' +
            '<div class="cart-actions">' +
              '<div class="stepper">' +
                '<button type="button" data-action="dec" data-id="' + esc(id) + '" aria-label="Убрать одну">−</button>' +
                '<span>' + qty + '</span>' +
                '<button type="button" data-action="inc" data-id="' + esc(id) + '" aria-label="Добавить ещё">+</button>' +
              '</div>' +
              '<button type="button" class="remove" data-action="remove" data-id="' + esc(id) + '">Удалить</button>' +
            '</div>' +
          '</div>' +
          '<strong>' + esc(money(product.price * qty)) + '</strong>' +
        '</div>'
      );
    }).join("");
    return (
      '<div class="panel-head"><h2>Корзина</h2>' +
        '<button type="button" class="text-btn" data-action="catalog">К товарам</button></div>' +
      lines +
      '<div class="total"><span>Итого</span><span>' + esc(money(total)) + '</span></div>'
    );
  }

  function matches(product, query) {
    var words = String(query || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return true;
    var hay = (product.name + " " + product.brand).toLowerCase();
    return words.every(function (word) { return hay.indexOf(word) !== -1; });
  }

  function money(value) {
    return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, "\u202f") + "\u00a0₽";
  }

  function bagIcon() {
    return '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M7 7.2 6.2 9H4.7c-.9 0-1.3 0-1.6.3-.2.3-.2.8-.1 1.6l.3 1.6c.4 2.4.6 3.6 1.4 4.3.8.7 2 .7 4.4.7h1.8c2.4 0 3.6 0 4.4-.7s1-1.9 1.4-4.3l.3-1.6c.1-.8.2-1.3-.1-1.6-.3-.3-.7-.3-1.6-.3H17.8L17 7.2a1 1 0 0 0-1.9.6L15.6 9H8.4l.5-1.2A1 1 0 0 0 7 7.2M10 13.2v2.2a1 1 0 1 1-2 0v-2.2a1 1 0 1 1 2 0m4.2-.2a1 1 0 0 1 1 1v2.2a1 1 0 1 1-2 0V14a1 1 0 0 1 1-1"/></svg>';
  }

  function esc(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function load() {
    try {
      var raw = sessionStorage.getItem("wpb-demo:" + theme);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || typeof data !== "object") return null;
      data.cart = data.cart && typeof data.cart === "object" ? data.cart : {};
      data.log = Array.isArray(data.log) ? data.log : [];
      data.view = data.view === "cart" ? "cart" : "catalog";
      data.query = typeof data.query === "string" ? data.query : "";
      return data;
    } catch (err) {
      return null;
    }
  }

  function save() {
    try {
      sessionStorage.setItem("wpb-demo:" + theme, JSON.stringify(state));
    } catch (err) {
      /* private mode */
    }
  }
})();
