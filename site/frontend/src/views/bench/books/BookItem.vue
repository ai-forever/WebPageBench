<template>
  <div v-if="ready" class="bench-books item-view">
    
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
    <div v-if="contentReady">
    <div class="container pt-2">
      <div v-if="item" class="breadcrumbs">
        <a href="javascript:void(0)">Книги</a>
        <span class="sep">/</span>
        <a href="javascript:void(0)">Аудиокниги</a>
        <span class="sep">/</span>
        <a href="javascript:void(0)">{{ mainGenre }}</a>
        <span class="sep">/</span>
        <a href="javascript:void(0)">{{ item.author }}</a>
        <span class="sep">/</span>
        <span class="current">📚 {{ item.name }}</span>
      </div>
      <v-row class="pt-4">
        <v-col cols="3 px-10">
          <div class="cover-wrap">
            <book-cover :item="item" />
            <div v-if="discountPercent" class="disc">-{{ discountPercent }}%</div>
          </div>
          <div class="side-panel">
            <div v-if="minAge || durationText" class="duration-row">
              <span class="label">Длительность книги</span>
              <span v-if="durationText" class="value">{{ durationText }}</span>
              <span v-if="minAge" class="age"> • {{ minAge }}+</span>
            </div>
            <v-btn class="listen-btn" block variant="outlined" @click="onFragmentClick">
              <v-icon size="18">{{ isCurrentAudio ? 'mdi-play-circle' : 'mdi-book-open-variant' }}</v-icon>
              <span>{{ isCurrentAudio ? 'Слушать фрагмент' : 'Читать фрагмент' }}</span>
            </v-btn>
            <v-btn class="subscribe-btn" block variant="outlined">Подписаться на новинки автора</v-btn>
            <div class="link-row">
              <v-icon size="16">mdi-book-check-outline</v-icon>
              <span>Отметить прослушанной</span>
            </div>
            <div class="link-row">
              <v-icon size="16">mdi-playlist-plus</v-icon>
              <span>Добавить в список</span>
            </div>
          </div>
        </v-col>
        <v-col cols="6">          
          <div v-if="item.is_sales_hit" class="hit-badge">Хит продаж</div>

          <div class="title pt-4">{{ item.name }}</div>
          <div class="subtitle">Автор <span class="author">{{ item.author }}</span></div>
          <div v-if="narrator" class="subtitle">Чтец <span class="narrator">{{ narrator }}</span></div>
          <div v-if="seriesInfo" class="series mt-4">{{ seriesInfo.art_order }} книга из {{ seriesInfo.arts_count }} в серии <span class="series-name">«{{ seriesInfo.name }}»</span></div>
          
          <!-- ITEM FORMAT SELECTOR -->
          <div class="format-row mt-6">
            <v-btn
              v-if="showTextButton"
              size="small"
              class="format-btn"
              :class="{ active: isCurrentText }"
              variant="outlined"
              @click="onTextClick"
            >
              <v-icon size="18">mdi-book-open-variant</v-icon>
              <span class="pl-2">Текст</span>
            </v-btn>
            <v-btn
              v-if="showAudioButton"
              size="small"
              class="format-btn"
              :class="{ active: isCurrentAudio }"
              variant="outlined"
              @click="onAudioClick"
            >
              <v-icon size="18">mdi-headphones</v-icon>
              <span class="pl-2">Аудио</span>
            </v-btn>
          </div>

          <!-- BUTTONS AND STATS -->

          <div class="stats-row styled">
            <div class="stat rating">
              <div class="top"><v-icon size="18" color="warning">mdi-star</v-icon><span class="value">{{ ratingDisplay }}</span></div>
              <div class="sub">{{ votesCount }} оценок</div>
            </div>
            <div class="divider" />
            <div class="stat">
              <div class="top"><span class="value">{{ reviewsCount }}</span></div>
              <div class="sub link">отзыва</div>
            </div>
            <div class="divider" />
            <div class="stat">
              <div class="top"><span class="value">{{ quotesCount }}</span></div>
              <div class="sub link">цитата</div>
            </div>
          </div>

          <!-- END BUTTONS AND STATS -->

          <div class="section-title mt-4">О книге</div>
          <div class="description">
            <span>{{ descriptionDisplay }}</span>
            <v-btn v-if="hasLongDescription" class="desc-toggle" variant="text" density="comfortable" @click="toggleDescription">{{ descExpanded ? 'Свернуть' : 'Далее' }}</v-btn>
          </div>

          <!-- <div v-if="hasAlternative" class="other-versions">
            <v-avatar size="56" rounded="sm">
              <v-img :src="item.cover_img_url" alt="alt"></v-img>
            </v-avatar>
            <div class="ov-content">
              <div class="ov-title">Другие версии</div>
              <div class="ov-subtitle">1 книга от 199 ₽</div>
            </div>
          </div> -->

          <div v-if="genres.length || tags.length" class="section-title mt-6">Жанры и теги</div>
          <div v-if="genres.length || tags.length" class="chips">
            <a v-for="(g, i) in genres" :key="'g'+i" href="javascript:void(0)" class="chip">{{ g }}</a>
            <a v-for="(t, i) in tags" :key="'t'+i" href="javascript:void(0)" class="chip">{{ t }}</a>
          </div>

          <div class="section-title mt-6">Отзывы <span class="count">{{ reviewsCount }}</span>
            <a href="javascript:void(0)" class="all-reviews">Смотреть все отзывы</a>
          </div>
          <v-select
            class="reviews-sort"
            :items="reviewSortItems"
            v-model="reviewSort"
            variant="outlined"
            density="comfortable"
            hide-details
          />
          <div class="reviews-list pt-6">
            <div v-for="rv in userReviews" :key="rv.id" class="review">
              <div class="body">
                <div class="meta">
                  <div class="left">
                    <v-avatar size="42"><v-icon size="28">mdi-account</v-icon></v-avatar>
                    <div>
                      <div class="author">{{ rv.user_display_name }}</div>
                      <div class="date">{{ formatDate(rv.created_at) }}</div>
                    </div>
                  </div>
                  <div class="right">
                    <span class="stars">★★★★★</span>
                  </div>
                </div>
                <div class="text pt-4" v-html="rv.text"></div>
                <div class="actions">
                  <span class="vote like">👍 {{ rv.likes_count || rv.likes_rating || 0 }}</span>
                  <span class="vote dislike">👎 {{ rv.dislikes_count || 0 }}</span>
                  <span class="reply">Ответить</span>
                  <span class="more">⋯</span>
                </div>
              </div>
            </div>
          </div>
        </v-col>
        <v-col cols="3 px-12">

          <!-- BUY CARD -->
          <div class="side-actions">
            <a href="javascript:void(0)" class="action" @click.prevent="addToFavorites">
              <v-icon size="18" :color="isFavorite ? 'red' : ''">{{ isFavorite ? 'mdi-heart' : 'mdi-heart-outline' }}</v-icon>
              <span>Отложить</span>
            </a>
            <a href="javascript:void(0)" class="action"><v-icon size="18">mdi-share-variant</v-icon><span>Поделиться</span></a>
          </div>
          <div class="buy-card">
            <div class="price">{{ priceWithCurrency }}</div>
            <template v-if="isPurchased">
              <v-btn class="primary" block><span>Слушать</span></v-btn>
            </template>
            <template v-else>
              <v-btn class="primary" block @click="buyNow"><span>Купить и скачать</span></v-btn>
              <!-- ADD TO BASKET -->
              <v-btn class="secondary" block @click="addToBasket">
                <div v-if="!inBasket">
                  <v-icon size="18">mdi-basket-outline</v-icon>
                  <span class="pl-2">Добавить в корзину</span>
                </div>
                <div v-else>
                  <div class="basket-in-label">В корзине</div>
                  <div class="basket-btn-subtitle">Перейти</div>
                </div>
              </v-btn>
            </template>
          </div>

          <div class="bonus-card px-6 mt-4">
            <div class="badge">Начислим +{{ earnedBonuses }}<span class="dot">◯</span></div>
            <div class="text">Покупайте книги и получайте бонусы.</div>
            <a href="javascript:void(0)" class="link">Участвовать в бонусной программе</a>
          </div>

          <div class="gift-card px-6 mt-4">
            <div class="gc-content">
              <div class="title">Подарите скидку 10%</div>
              <div class="desc"><a href="javascript:void(0)" class="link">Посоветуйте</a> эту книгу и получите 74,91 ₽ с покупки её другом.</div>
              <a href="javascript:void(0)" class="link">Подробнее</a>
            </div>
          </div>

          <!-- END BUY CARD -->
        </v-col>
      </v-row>
      
    </div>
</div>

    <v-dialog v-model="basketPromoOpen" max-width="480">
      <v-card class="promo-card">
        <div class="promo-header">
          <div class="promo-title">Купите три книги одновременно и выберите четвёртую в подарок</div>
          <v-btn icon variant="text" class="promo-close" @click="basketPromoOpen = false"><v-icon size="20">mdi-close</v-icon></v-btn>
        </div>
        <div class="promo-body">
          <div class="promo-equation">
            <div class="promo-slot">1</div>
            <div class="promo-plus">+</div>
            <div class="promo-slot">2</div>
            <div class="promo-plus">+</div>
            <div class="promo-slot">3</div>
            <div class="promo-eq">=</div>
            <div class="promo-gift"></div>
          </div>
          <a href="javascript:void(0)" class="promo-terms">Условия акции</a>
        </div>
        <div class="promo-footer">Чтобы воспользоваться акцией, добавьте нужные книги в корзину.</div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";

import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import BookCover from "./BookCover.vue";
import { isLoggedIn, addBasketItem, setCurrentUsername, getBasketItems, getCurrentUsername, getPurchasedItems, clearBasket, isBooksFavorite, toggleBooksFavorite } from "@/utils/localCache.js";
import { _logActivity } from "@/common/trackHelper";
import { ensureBenchDomainMerged, navigateToBooksBasket, pushBenchRoute } from "@/common/benchNavigation";
import { isUnifiedBench } from "@/common/benchTheme";

import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksBookItem",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, LoginDialog, BookCover },
  data() {
    return {
      loginDialog: false,
      descExpanded: false,
      reviewSort: 'popular',
      loggedIn: false,
      basketKeys: [],
      purchasedKeys: [],
      basketPromoOpen: false,
      selectedFormat: 'text',
      favoritesUpdate: 0 };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() { return this.loggedIn; },
    ready() {
      return this.item;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    showBasketPopup() {
      return !!(this.testData && this.testData.show_basket_popup === true);
    },
    itemKey() {
      return this.$route.params.state_id;
    },
    username() {
      const stored = getCurrentUsername && getCurrentUsername();
      if (stored) return stored;
      const cfgUser = this.testData && this.testData.login_data && this.testData.login_data.login;
      return cfgUser || 'guest';
    },
    item() {
      return (this.kvStore && this.kvStore[this.itemKey]) || null;
    },
    inBasket() {
      return (this.basketKeys || []).includes(this.itemKey);
    },
    isPurchased() {
      return (this.purchasedKeys || []).includes(this.itemKey);
    },
    isFavorite() {
      // Force reactivity update
      this.favoritesUpdate;
      const username = this.loggedIn ? this.username : 'guest';
      return isBooksFavorite(username, this.itemKey);
    },
    minAge() {
      const v = this.item && this.item.min_age;
      return v != null ? v : '';
    },
    durationText() {
      const symbols = this.item && this.item.symbols_count;
      if (!symbols) return '';
      const totalMinutes = Math.max(1, Math.round((symbols / 10000) * 60 * 0.35));
      const hours = Math.floor(totalMinutes / 60);
      const minutes = totalMinutes % 60;
      const h = hours > 0 ? `${hours} ч` : '';
      const m = `${minutes} мин.`;
      return [h, m].filter(Boolean).join(' ');
    },
    narrator() {
      const persons = (this.item && this.item.persons) || [];
      const reader = persons.find(p => p && p.role === "reader");
      return reader && reader.full_name ? reader.full_name : "";
    },
    seriesInfo() {
      const series = (this.item && this.item.series) || [];
      return series && series.length > 0 ? series[0] : null;
    },
    mainGenre() {
      const genres = this.item && this.item.genres;
      if (genres && genres.length > 0) {
        return genres[0].name.charAt(0).toUpperCase() + genres[0].name.slice(1);
      }
      return "";
    },
    rating() {
      if (!this.item || this.item.rating == null) return "";
      return Number(this.item.rating).toFixed(1);
    },
    ratingDisplay() {
      if (!this.rating) return '';
      return String(this.rating).replace('.', ',');
    },
    votesCount() {
      if (!this.item) return "";
      const byTop = this.item.number_of_votes;
      return byTop != null ? byTop : "";
    },
    quotesCount() {
      const q = this.item && this.item.quotes_count;
      return q != null ? q : 0;
    },
    discountPercent() {
      const top = this.item && this.item.discount_percent;
      const nested = this.item && this.item.prices && this.item.prices.discount_percent;
      return top != null ? top : (nested != null ? nested : 0);
    },
    priceWithCurrency() {
      if (!this.item) return "";
      const nestedPrices = this.item.prices;
      const price = nestedPrices && nestedPrices.final_price != null ? nestedPrices.final_price : (this.item.price != null ? this.item.price : 0);
      const currencyCode = (nestedPrices && nestedPrices.currency) || this.item.currency;
      const currency = currencyCode === "RUB" ? "₽" : (currencyCode || "");
      return `${price}${currency ? " " + currency : ""}`;
    },
    earnedBonuses() {
      const p = this.item && this.item.prices;
      return (p && p.can_earned_bonuses_amount_after_sign_up_loyalty) || 22;
    },
    shortDescription() {
      // take plain text from html_annotation
      const html = this.item && this.item.html_annotation;
      if (!html) return "";
      const text = html
        .replace(/<[^>]+>/g, " ")
        .replace(/\s+/g, " ")
        .trim();
      return text;
    },
    hasLongDescription() {
      return this.shortDescription && this.shortDescription.length > 300;
    },
    descriptionDisplay() {
      if (!this.hasLongDescription) return this.shortDescription;
      return this.descExpanded ? this.shortDescription : this.shortDescription.slice(0, 300) + '…';
    },
    genres() {
      const genres = (this.item && this.item.genres) || [];
      return genres.map(g => g && g.name).filter(Boolean);
    },
    tags() {
      const tags = (this.item && this.item.tags) || [];
      return tags.map(t => t && t.name).filter(Boolean);
    },
    hasAlternative() {
      return !!(this.item && this.item.alternative_version);
    },
    altItemKey() {
      const alt = this.item && this.item.alternative_version;
      const altId = alt && alt.id;
      return altId != null ? `item_${altId}` : null;
    },
    altItem() {
      if (!this.altItemKey) return null;
      return (this.kvStore && this.kvStore[this.altItemKey]) || null;
    },
    isCurrentAudio() {
      return !!(this.item && this.item.is_audiobook);
    },
    isCurrentText() {
      return !!(this.item && !this.item.is_audiobook);
    },
    showTextButton() {
      if (this.isCurrentText) return true;
      const alt = this.altItem;
      return !!(alt && alt.is_audiobook === false);
    },
    showAudioButton() {
      if (this.isCurrentAudio) return true;
      const alt = this.altItem;
      return !!(alt && alt.is_audiobook === true);
    },
    textButtonNavigatesToAlt() {
      return this.isCurrentAudio && this.altItem && this.altItem.is_audiobook === false;
    },
    audioButtonNavigatesToAlt() {
      return this.isCurrentText && this.altItem && this.altItem.is_audiobook === true;
    },
    reviews() {
      return (this.item && this.item.reviews) || [];
    },
    reviewsCount() {
      const direct = this.item && this.item.reviews_count;
      if (direct != null) return direct;
      return this.reviews.length;
    },
    reviewSortItems() {
      return [
        { title: 'Сначала популярные', value: 'popular' },
        { title: 'Сначала новые', value: 'new' },
      ];
    },
    userReviews() {
      return this.reviews;
    }
  },
  watch: {
    item: {
      immediate: true,
      handler(newVal) {
        if (!newVal) return;
        this.selectedFormat = newVal.is_audiobook ? 'audio' : 'text';
      }
    }
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    toggleDescription() { this.descExpanded = !this.descExpanded; },
    onFragmentClick() {
      const fragmentType = this.isCurrentAudio ? 'listen_fragment' : 'read_fragment';
      _logActivity(this, {
        type: 'button_clicked',
        item_id: this.itemKey,
        button_type: fragmentType });
    },
    selectFormat(format) {
      this.selectedFormat = format;
    },
    onTextClick() {
      if (this.textButtonNavigatesToAlt && this.altItemKey) {
        this.navigateToItem(this.altItemKey);
      } else {
        this.selectFormat('text');
      }
    },
    onAudioClick() {
      if (this.audioButtonNavigatesToAlt && this.altItemKey) {
        this.navigateToItem(this.altItemKey);
      } else {
        this.selectFormat('audio');
      }
    },
    navigateToItem(stateId) {
      pushBenchRoute(this.$router, {
        name: 'bench_books_item',
        stateId: stateId,
        trackId: this.$route.params.track_id });
    },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      // Merge guest basket into user basket on login
      try {
        const guestItems = getBasketItems('guest');
        if (Array.isArray(guestItems) && guestItems.length > 0) {
          for (const k of guestItems) {
            addBasketItem(username, k);
          }
          // Clear guest basket after merge
          clearBasket('guest');
        }
      } catch (e) {}
      this.refreshBasket();
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          if (isUnifiedBench(this.trackConfig)) {
            ensureBenchDomainMerged('books');
          }
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          this.loggedIn = isLoggedIn();
          this.applyStateDelay();
        });
    },
    goToBasket() {
      navigateToBooksBasket(this.$router, this.$route.params.track_id);
    },
    addToBasket() {
      if (!this.itemKey) return;
      if (this.inBasket) {
        this.goToBasket();
        return;
      }
      const username = this.loggedIn ? this.username : 'guest';
      addBasketItem(username, this.itemKey);
      _logActivity(this, this.buildBasketAddEvent());
      this.refreshBasket();
      if (this.showBasketPopup) {
        this.basketPromoOpen = true;
      }
    },
    buyNow() {
      // Add to basket and go to purchase
      if (!this.loggedIn) {
        this.openLoginDialog();
        return;
      }
      if (!this.inBasket) {
        const username = this.username;
        addBasketItem(username, this.itemKey);
        _logActivity(this, this.buildBasketAddEvent());
      }
      this.refreshBasket();
      pushBenchRoute(this.$router, {
        name: 'bench_books_purchase',
        stateId: 'state_purchase',
        trackId: this.$route.params.track_id });
    },
    refreshBasket() {
      const username = this.loggedIn ? this.username : 'guest';
      this.basketKeys = getBasketItems(username);
      this.purchasedKeys = this.loggedIn ? getPurchasedItems(this.username) : [];
    },
    formatDate(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      const months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
      return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
    },
    buildBasketAddEvent() {
      const item = this.item;
      const nestedPrices = item && item.prices;
      const price = nestedPrices && nestedPrices.final_price != null
        ? nestedPrices.final_price
        : (item && item.price != null ? item.price : null);
      const genres = (item && item.genres) || [];
      const mainGenre = genres.length > 0 && genres[0].name ? genres[0].name : null;

      return {
        type: 'basket_add',
        item_id: this.itemKey,
        title: item && item.name ? item.name : null,
        author: item && item.author ? item.author : null,
        price: price,
        is_audiobook: item && item.is_audiobook === true,
        genre: mainGenre
      };
    },
    addToFavorites() {
      const username = this.loggedIn ? this.username : 'guest';
      const wasAlreadyFavorite = this.isFavorite;
      toggleBooksFavorite(username, this.itemKey);
      this.favoritesUpdate++;

      const item = this.item;
      const nestedPrices = item && item.prices;
      const price = nestedPrices && nestedPrices.final_price != null
        ? nestedPrices.final_price
        : (item && item.price != null ? item.price : null);
      const genres = (item && item.genres) || [];
      const mainGenre = genres.length > 0 && genres[0].name ? genres[0].name : null;

      _logActivity(this, {
        type: wasAlreadyFavorite ? 'remove_favorites' : 'add_favorites',
        item_id: this.itemKey,
        title: item && item.name ? item.name : null,
        author: item && item.author ? item.author : null,
        price: price,
        is_audiobook: item && item.is_audiobook === true,
        genre: mainGenre
      });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      if (isUnifiedBench(this.trackConfig)) {
        ensureBenchDomainMerged('books');
      }
      const kvPath = this.testData.kv_store_path || '';
      if (kvPath && !this.item) {
        this.$store.dispatch(GET_KV_STORE, { kvPath });
      }
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.refreshBasket();
  }
});
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }

/* Promo dialog styling */
.promo-card { border-radius: 16px; overflow: hidden; }
.promo-header { background: #f3eefb; position: relative; padding: 30px 34px 0 34px; }
.promo-title { font-size: 20px; font-weight: 800; color: #111; line-height: 1.25; max-width: 620px; }
.promo-close { position: absolute; top: 8px; right: 8px; color: #888; }
.promo-body { background: #f3eefb; padding: 12px 34px 24px 34px; }
.promo-equation { display: flex; align-items: center; gap: 14px; margin: 6px 0 10px 0; }
.promo-slot { width: 64px; height: 86px; border: 2px dashed #cfc4e4; border-radius: 12px; display: flex; align-items: center; justify-content: center; background: #fff; color: #7a6bb3; font-weight: 700; font-size: 20px; }
.promo-plus, .promo-eq { color: #6d6597; font-weight: 700; font-size: 22px; }
.promo-gift { width: 68px; height: 86px; border-radius: 10px; background: linear-gradient(180deg, #ffb06b 0%, #ff7d59 100%); position: relative; transform: rotate(-12deg); box-shadow: 0 4px 10px rgba(0,0,0,0.12); }
.promo-gift::before { content: ""; position: absolute; left: 50%; top: 0; transform: translateX(-50%); width: 16px; height: 100%; background: #4b51c2; border-radius: 4px; }
.promo-gift::after { content: ""; position: absolute; left: 0; right: 0; top: 42%; height: 16px; background: #4b51c2; border-radius: 4px; }
.promo-terms { color: #5b6ee1; font-weight: 500; text-decoration: none; font-size: 14px; }
.promo-footer { background: #fff; padding: 24px 34px 32px 34px; font-size: 16px; color: #000000; font-weight: 500; }
/* Format buttons: ellipsis on narrow widths */
.format-row .format-btn { max-width: 100%; overflow: hidden; min-width: 0; }
.side-panel .v-btn { max-width: 100%; }
.buy-card .v-btn {
  max-width: 100%;
  pointer-events: auto;
}
.buy-card .v-btn :deep(.v-btn__overlay),
.buy-card .v-btn :deep(.v-btn__underlay) {
  pointer-events: none;
}
.buy-card .secondary :deep(.v-btn__content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  white-space: normal;
}
.buy-card .basket-in-label {
  font-weight: 800;
  line-height: 1.2;
}
</style>
