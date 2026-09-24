<template>
  <div v-if="configLoaded" class="bench-books">    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      :prefill-query="query"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>
    <div v-if="contentReady">
    <!-- MAIN SECTION -->
    <div class="search-section">
      <div class="search-layout">
        <div class="filters-panel">
          <div class="filter-row">
            <!-- <v-icon size="16" class="info">mdi-information-outline</v-icon> -->
            <div class="filter-label">Доступно по подписке </div>
            <v-switch v-model="filters.onlySubscription" inset density="compact" color="indigo-darken-4" hide-details></v-switch>
          </div>
          <div class="filter-row">
            <!-- <v-icon size="16" class="info">mdi-information-outline</v-icon> -->
            <div class="filter-label">Доступно в абонементе </div>
            <v-switch v-model="filters.inAbonement" inset density="compact" color="indigo-darken-3" hide-details></v-switch>
          </div>

          <div class="filter-group-title">Формат</div>
          <v-checkbox v-model="filters.formats.text" label="Текст" density="compact" hide-details></v-checkbox>
          <v-checkbox v-model="filters.formats.audio" label="Аудио" density="compact" hide-details></v-checkbox>
          <v-checkbox v-model="filters.formats.podcast" label="Подкаст" density="compact" hide-details></v-checkbox>

          <div class="filter-group-title">Язык</div>
          <div v-for="code in languagesAvailable" :key="code">
            <v-checkbox v-model="languagesSelected" :value="code" :label="languageLabel(code)" density="compact" hide-details></v-checkbox>
          </div>

          <div class="filter-row">
            <div class="filter-label">
              Высокая оценка
              <div class="filter-caption">Книги с рейтингом 4 и 5 звёзд</div>
            </div>
            <v-switch v-model="filters.highRating" inset density="compact" color="indigo-darken-3" hide-details></v-switch>
          </div>
          <div class="filter-row">
            <div class="filter-label">Авторы</div>
            <v-switch v-model="filters.platformAuthors" inset density="compact" color="indigo-darken-3" hide-details></v-switch>
          </div>
          <div class="filter-row">
            <div class="filter-label">Эксклюзивы</div>
            <v-switch v-model="filters.exclusives" inset density="compact" color="indigo-darken-3" hide-details></v-switch>
          </div>
        </div>
        <div class="container">
          <div class="search-label">
            {{ searchTitle }}
          </div>
          <div v-if="visibleItems.length" class="results-grid">
            <div class="book-card product product-card" v-for="it in visibleItems" :key="(it.id || it.uuid || it.name) + (it.is_audiobook ? '-a' : '-t')" role="button" tabindex="0" @click="onItemClick(it)">
              <div class="thumb" @click="onItemClick(it)">
                <book-cover :item="it" />
                <div v-if="it.is_sales_hit" class="hit-badge">Хит продаж</div>
                <div v-if="it.discount_percent" class="discount-badge">-{{ it.discount_percent }}%</div>
                <v-btn
                  class="favorite"
                  variant="text"
                  size="small"
                  @click.stop="onFavoriteClick(it)"
                >
                  <v-icon size="18" :color="isItemFavorite(it) ? 'red' : ''">
                    {{ isItemFavorite(it) ? 'mdi-heart' : 'mdi-heart-outline' }}
                  </v-icon>
                </v-btn>
              </div>
              <div class="name" @click="onItemClick(it)">{{ it.name || it.title }}</div>
              <div v-if="it.author" class="author">{{ it.author }}</div>
              <div class="meta">
                <div class="formats">
                  <v-icon v-if="it.is_audiobook" size="18">mdi-headphones</v-icon>
                  <v-icon v-else size="18">mdi-book-open-variant</v-icon>
                </div>
                <div class="rating">
                  <v-icon size="16" color="warning">mdi-star</v-icon>
                  <span class="rating-value">{{ formatRating(it.rating) }}</span>
                  <span class="votes">{{ it.number_of_votes }}</span>
                </div>
              </div>
              <div class="price-row">
                <div class="price-current">{{ formatCurrency(getCurrentPrice(it), getCurrency(it)) }}</div>
                <div v-if="getBasePrice(it) !== getCurrentPrice(it)" class="price-old">{{ formatCurrency(getBasePrice(it), getCurrency(it)) }}</div>
              </div>
            </div>
          </div>
          <div v-if="hasMore" class="show-more-wrap">
            <v-btn variant="flat" @click="showMore">Показать ещё</v-btn>
          </div>
        </div>
      </div>
    </div>
    <!-- END MAIN SECTION -->
</div>
  </div>
  <div v-else />
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import BookCover from "./BookCover.vue";
import { getCurrentUsername, isLoggedIn, isBooksFavorite, toggleBooksFavorite } from "@/utils/localCache.js";
import { pushBenchRoute } from "@/common/benchNavigation";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { _logActivity } from "@/common/trackHelper";

export default defineComponent({
  name: "BooksSearch",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, LoginDialog, BookCover },
  props: {
    prefillQuery: { type: String, default: "" }
  },
  data() {
    return { isLoading: false, loginDialog: false, loggedIn: false, favoritesUpdate: 0, itemsSearchList: [], foundItemsAll: [], showCount: 10,
      filters: {
        onlySubscription: false,
        inAbonement: false,
        exclusives: false,
        highRating: false,
        platformAuthors: false,
        formats: { text: false, audio: false, podcast: false }
      },
      languagesSelected: [] };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          this.loggedIn = isLoggedIn();
          this.applyStateDelay();
        });
    },
    buildItemsList() {
      try {
        const kv = this.kvStore || {};
        const list = [];
        Object.keys(kv).forEach(key => {
          const it = kv[key];
          if (!it) return;
          const name = it.name || it.title || '';
          const author = it.author || '';
          const label = [name, author].filter(Boolean).join(' ');
          if (label) list.push({ key, label: String(label), item: it });
        });
        this.itemsSearchList = list;
      } catch(e) {
        this.itemsSearchList = [];
      }
    },
    tokenize(text) {
      return String(text || "")
        .toLowerCase()
        .split(/[^0-9a-zа-яё]+/i)
        .filter((w) => w.length >= 2);
    },
    editDistance(a, b) {
      if (a === b) return 0;
      if (Math.abs(a.length - b.length) > 1) return 99;
      const rows = a.length + 1;
      const cols = b.length + 1;
      const prev = new Array(cols);
      const cur = new Array(cols);
      for (let j = 0; j < cols; j += 1) prev[j] = j;
      for (let i = 1; i < rows; i += 1) {
        cur[0] = i;
        for (let j = 1; j < cols; j += 1) {
          const cost = a[i - 1] === b[j - 1] ? 0 : 1;
          cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
        }
        for (let j = 0; j < cols; j += 1) prev[j] = cur[j];
      }
      return prev[b.length];
    },
    wordHitsToken(word, token) {
      if (token === word) return 100;
      if (token.startsWith(word) || (word.startsWith(token) && token.length >= 4)) return 70;
      if (word.length >= 4 && token.includes(word)) return 50;
      if (word.length >= 4 && token.length >= 4 && this.editDistance(word, token) <= 1) return 40;
      return 0;
    },
    scoreLabel(query, label) {
      const q = String(query || "").trim().toLowerCase();
      const t = String(label || "").toLowerCase();
      if (!q || !t) return 0;
      const qWords = this.tokenize(q);
      const tokens = this.tokenize(t);
      if (!qWords.length || !tokens.length) return 0;
      let sc = t.includes(q) ? 200 : 0;
      for (const w of qWords) {
        let best = 0;
        for (const tok of tokens) best = Math.max(best, this.wordHitsToken(w, tok));
        if (best === 0) return 0;
        sc += best;
      }
      return sc;
    },
    runSearch() {
      const q = this.query;
      if (!q) {
        this.foundItemsAll = [];
        return;
      }
      const ranked = this.itemsSearchList
        .map(x => ({ ...x, sc: this.scoreLabel(q, x.label) }))
        .filter(x => x.sc > 0)
        .sort((a,b) => b.sc - a.sc);
      this.foundItemsAll = ranked.map(x => x.item);
    },
    showMore() { this.showCount += 10; },
    formatRating(value) {
      if (value === null || value === undefined || isNaN(Number(value))) return '';
      return Number(value).toFixed(1);
    },
    getCurrency(item) {
      const nested = item && item.prices && item.prices.currency;
      return nested || (item && item.currency) || 'RUB';
    },
    getCurrentPrice(item) {
      if (!item) return 0;
      const p = item.prices;
      if (p && p.final_price != null) return p.final_price;
      return item.price != null ? item.price : 0;
    },
    getBasePrice(item) {
      if (!item) return 0;
      const p = item.prices;
      const base = p && (p.base_price != null ? p.base_price : p.old_price);
      if (base != null) return base;
      return this.getCurrentPrice(item);
    },
    discountPercent(item) {
      const top = item && item.discount_percent;
      const nested = item && item.prices && item.prices.discount_percent;
      return top != null ? top : (nested != null ? nested : 0);
    },
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (currencyCode === 'RUB' || currencyCode === 'RUR' || currencyCode === '₽' || !currencyCode) {
        const formatted = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim();
    },
    languageLabel(code) {
      const map = { ru: 'Русский', en: 'Английский', de: 'Немецкий', fr: 'Французский', es: 'Испанский' };
      const key = String(code || '').toLowerCase();
      return map[key] || key.toUpperCase();
    },
    onItemClick(item) {
      if (!item) return;
      const toView = item.to_view_type || item.to_type || 'bench_books_item';
      const toState = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : undefined);
      if (toState) {
        pushBenchRoute(this.$router, {
          name: toView,
          stateId: toState,
          trackId: this.$route.params.track_id });
      }
    },
    isItemFavorite(item) {
      this.favoritesUpdate;
      if (!item) return false;
      const itemId = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : null);
      if (!itemId) return false;
      const username = getCurrentUsername() || 'guest';
      return isBooksFavorite(username, itemId);
    },
    onFavoriteClick(item) {
      if (!item) return;
      const itemId = item.to_state || item.kv_id || (item.id ? `item_${item.id}` : null);
      if (!itemId) return;
      const username = getCurrentUsername() || 'guest';
      const wasAlreadyFavorite = isBooksFavorite(username, itemId);
      toggleBooksFavorite(username, itemId);
      this.favoritesUpdate++;
      const nestedPrices = item.prices;
      const price = nestedPrices && nestedPrices.final_price != null
        ? nestedPrices.final_price
        : (item.price != null ? item.price : null);
      const genres = item.genres || [];
      const mainGenre = genres.length > 0 && genres[0].name ? genres[0].name : null;
      _logActivity(this, {
        type: wasAlreadyFavorite ? 'remove_favorites' : 'add_favorites',
        item_id: itemId,
        title: item.name || item.title || null,
        author: item.author || null,
        price,
        is_audiobook: item.is_audiobook === true,
        genre: mainGenre });
    } },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() { return this.loggedIn; },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    query() {
      return (this.$route && this.$route.query && this.$route.query.q) || '';
    },
    searchTitle() {
      const q = this.query;
      if (q) return `Результаты поиска «${q}»`;
      return 'Результаты поиска';
    },
    languagesAvailable() {
      const set = new Set();
      const kv = this.kvStore || {};
      Object.keys(kv).forEach(k => {
        const it = kv[k];
        const lc = it && it.language_code;
        if (lc) set.add(String(lc).toLowerCase());
      });
      return Array.from(set).sort();
    },
    filteredItems() {
      const list = this.foundItemsAll || [];
      const f = this.filters || {};
      const fm = (f.formats) || {};
      const anyFormat = !!(fm.text || fm.audio || fm.podcast);
      const langSel = this.languagesSelected || [];
      const langSet = new Set(langSel.map(x => String(x).toLowerCase()));
      return list.filter(it => {
        if (f.onlySubscription && !it.is_available_with_subscription) return false;
        if (f.inAbonement && !it.is_abonement_art) return false;
        if (f.exclusives && !it.is_exclusive) return false;
        if (f.highRating && !(Number(it.rating) >= 4)) return false;
        if (f.platformAuthors && !it.is_platform_author) return false;

        if (anyFormat) {
          const isAudio = !!it.is_audiobook;
          const isPodcast = !!it.is_podcast;
          const isText = !isAudio && !isPodcast;
          const matches = (fm.audio && isAudio) || (fm.podcast && isPodcast) || (fm.text && isText);
          if (!matches) return false;
        }

        if (langSet.size > 0) {
          const lc = String(it.language_code || '').toLowerCase();
          if (!langSet.has(lc)) return false;
        }
        return true;
      });
    },
    visibleItems() { return (this.filteredItems || []).slice(0, this.showCount); },
    hasMore() { return (this.filteredItems || []).length > this.showCount; }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.buildItemsList();
    this.runSearch();
  },
  watch: {
    kvStore: {
      deep: true,
      handler() { this.buildItemsList(); this.runSearch(); }
    },
    query() { this.runSearch(); },
    "filters.onlySubscription"(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "subscription", value: val });
    },
    "filters.inAbonement"(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "abonement", value: val });
    },
    "filters.exclusives"(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "exclusives", value: val });
    },
    "filters.highRating"(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "high_rating", value: val });
    },
    "filters.platformAuthors"(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "platform_authors", value: val });
    },
    "filters.formats": {
      deep: true,
      handler(val) {
        this.showCount = 10;
        const selectedFormats = [];
        if (val.text) selectedFormats.push("text");
        if (val.audio) selectedFormats.push("audio");
        if (val.podcast) selectedFormats.push("podcast");
        _logActivity(this, { type: "apply_filter", filter_type: "format", value: selectedFormats });
      }
    },
    languagesSelected(val) {
      this.showCount = 10;
      _logActivity(this, { type: "apply_filter", filter_type: "language", value: [...val] });
    }
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }
.search-section { max-width: var(--shop-max-width); margin: 24px auto; padding: 0 16px; }
.search-layout { display: grid; grid-template-columns: 280px 1fr; gap: 24px; }
.filters-panel { background: #fff; padding: 12px; height: fit-content; }
.filter-group-title { margin-top: 16px; margin-bottom: 8px; font-weight: 800; color: #15223b; }
.filter-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 0; }
.filter-label { font-weight: 700; color: #15223b; }
.filter-caption { font-size: 12px; color: #6b7280; font-weight: 400; }
.search-label { font-size: 28px; font-weight: 800; color: #15223b; }
.results-grid { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 16px; margin-top: 16px; }
.book-card { background: #fff; border: 0px; padding-bottom: 12px; border-radius: 14px; }
.book-card .thumb { position: relative; width: 100%; cursor: pointer; border-radius: 12px; overflow: hidden; }
.book-card .thumb .disc { position: absolute; left: 8px; top: 8px; background: #ef4444; color: #fff; font-weight: 800; border-radius: 12px; padding: 2px 6px; font-size: 12px; }
.book-card .name { font-weight: 800; font-size: 14px; padding: 8px 12px 0 12px; cursor: pointer; line-height: 1.2; }
.book-card .author { color: #364152; font-size: 13px; padding: 2px 12px 0 12px; opacity: .8; }
.book-card .meta { display: flex; align-items: center; justify-content: space-between; padding: 6px 12px 0 12px; }
.book-card .formats { display: flex; gap: 8px; color: #4a4a4a; }
.book-card .rating { display: flex; align-items: center; gap: 4px; color: #1f1f1f; }
.book-card .rating .votes { opacity: .7; }
.book-card .price-row { display: flex; align-items: center; gap: 8px; padding: 8px 12px 0 12px; }
.book-card .price-current { font-weight: 800; color: #111827; }
.book-card .price-old { color: #9ca3af; text-decoration: line-through; }
.show-more-wrap { display: flex; justify-content: center; margin-top: 16px; }
</style>


