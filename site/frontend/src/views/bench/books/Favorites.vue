<template>
  <div v-if="configLoaded" class="bench-books">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>
    <div v-if="contentReady" class="fav-section">
      <div class="search-label">Избранное</div>
      <div v-if="visibleItems.length" class="results-grid">
        <div
          class="book-card product product-card"
          v-for="it in visibleItems"
          :key="it.to_state || it.kv_id"
          role="button"
          tabindex="0"
          @click="onItemClick(it)"
        >
          <div class="thumb" @click="onItemClick(it)">
            <book-cover :item="it" />
            <div v-if="it.is_sales_hit" class="hit-badge">Хит продаж</div>
            <div v-if="it.discount_percent" class="discount-badge">-{{ it.discount_percent }}%</div>
            <v-btn class="favorite" variant="text" size="small" @click.stop="onFavoriteClick(it)">
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
              <v-icon size="18">mdi-book-open-variant</v-icon>
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
      <div v-else class="no-results">Пока пусто. Нажмите сердце на карточке книги, чтобы добавить сюда.</div>
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
import { getCurrentUsername, isLoggedIn, setCurrentUsername, getBooksFavorites, isBooksFavorite, toggleBooksFavorite } from "@/utils/localCache.js";
import { pushBenchRoute } from "@/common/benchNavigation";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { _logActivity } from "@/common/trackHelper";

export default defineComponent({
  name: "BooksFavorites",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, LoginDialog, BookCover },
  data() {
    return { loginDialog: false, loggedIn: false, favoritesUpdate: 0 };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || "guest";
      setCurrentUsername(username);
      this.loginDialog = false;
      this.favoritesUpdate++;
    },
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
    formatRating(value) {
      if (value === null || value === undefined || isNaN(Number(value))) return "";
      return Number(value).toFixed(1);
    },
    getCurrency(item) {
      const nested = item && item.prices && item.prices.currency;
      return nested || (item && item.currency) || "RUB";
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
    formatCurrency(value, currencyCode) {
      const num = Number(value || 0);
      if (currencyCode === "RUB" || currencyCode === "RUR" || currencyCode === "₽" || !currencyCode) {
        const formatted = num.toLocaleString("ru-RU", { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 });
        return `${formatted}\u00A0₽`;
      }
      return `${num.toLocaleString("ru-RU")} ${currencyCode}`.trim();
    },
    itemKey(item) {
      if (!item) return null;
      return item.to_state || item.kv_id || (item.id ? `item_${item.id}` : null);
    },
    onItemClick(item) {
      const toState = this.itemKey(item);
      if (!toState) return;
      pushBenchRoute(this.$router, {
        name: item.to_view_type || "bench_books_item",
        stateId: toState,
        trackId: this.$route.params.track_id,
      });
    },
    isItemFavorite(item) {
      this.favoritesUpdate;
      const itemId = this.itemKey(item);
      if (!itemId) return false;
      return isBooksFavorite(getCurrentUsername() || "guest", itemId);
    },
    onFavoriteClick(item) {
      const itemId = this.itemKey(item);
      if (!itemId) return;
      const username = getCurrentUsername() || "guest";
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
        type: wasAlreadyFavorite ? "remove_favorites" : "add_favorites",
        item_id: itemId,
        title: item.name || item.title || null,
        author: item.author || null,
        price,
        is_audiobook: item.is_audiobook === true,
        genre: mainGenre,
      });
    },
  },
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
    visibleItems() {
      this.favoritesUpdate;
      const kv = this.kvStore || {};
      const username = getCurrentUsername() || "guest";
      const keys = getBooksFavorites(username) || [];
      return keys.map((key) => {
        const item = kv[key];
        if (!item) return null;
        return { ...item, to_state: key, kv_id: key };
      }).filter(Boolean);
    },
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
  },
});
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }
.fav-section { max-width: var(--shop-max-width); margin: 24px auto; padding: 0 16px 40px; }
.search-label { font-size: 28px; font-weight: 800; color: #15223b; }
.results-grid { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 16px; margin-top: 16px; }
.book-card { background: #fff; border: 0px; padding-bottom: 12px; border-radius: 14px; }
.book-card .thumb { position: relative; width: 100%; cursor: pointer; border-radius: 12px; overflow: hidden; }
.book-card .name { font-weight: 800; font-size: 14px; padding: 8px 12px 0 12px; cursor: pointer; line-height: 1.2; }
.book-card .author { color: #364152; font-size: 13px; padding: 2px 12px 0 12px; opacity: .8; }
.book-card .meta { display: flex; align-items: center; justify-content: space-between; padding: 6px 12px 0 12px; }
.book-card .formats { display: flex; gap: 8px; color: #4a4a4a; }
.book-card .rating { display: flex; align-items: center; gap: 4px; color: #1f1f1f; }
.book-card .rating .votes { opacity: .7; }
.book-card .price-row { display: flex; align-items: center; gap: 8px; padding: 8px 12px 0 12px; }
.book-card .price-current { font-weight: 800; color: #111827; }
.book-card .price-old { color: #9ca3af; text-decoration: line-through; }
.no-results { font-size: 16px; color: #6b7280; margin-top: 24px; }
@media (max-width: 1100px) {
  .results-grid { grid-template-columns: repeat(3, minmax(0,1fr)); }
}
@media (max-width: 800px) {
  .results-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
</style>
