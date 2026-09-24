<template>
  <div class="bench-market-header">
    <!-- Grey overlay over the whole page when search is focused -->
    <div v-if="searchFocused" class="bench-market-overlay" @click="onOverlayClick"></div>
    <div class="panel">
      <div class="container">
      <v-btn class="catalog" variant="flat" @click="onCatalogClick">
        <template #prepend>
          <span class="catalog-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" class="catalog-svg"><path fill="currentColor" d="M4 7.556C4 4.628 4.628 4 7.556 4s3.555.628 3.555 3.556-.627 3.555-3.555 3.555S4 10.484 4 7.556m0 8.888c0-2.928.628-3.555 3.556-3.555s3.555.627 3.555 3.555S10.484 20 7.556 20 4 19.372 4 16.444M16.444 4c-2.928 0-3.555.628-3.555 3.556s.627 3.555 3.555 3.555S20 10.484 20 7.556 19.372 4 16.444 4m-3.555 12.444c0-2.928.627-3.555 3.555-3.555S20 13.516 20 16.444 19.372 20 16.444 20s-3.555-.628-3.555-3.556"/></svg>
          </span>
        </template>
        {{ catalogLabel }}
      </v-btn>
      <div class="search-container" :class="{ 'search-container-with-tags': showSuggestionTags }">
        <div class="search" :class="searchVariantClass">
          <!-- CATEGORY SELECTOR -->
          <div
            class="scope"
            :class="{ selected: !!selectedScope }"
            role="button"
            tabindex="0"
            @click="openCategoryPanel"
            @keydown.enter.prevent="openCategoryPanel"
          >
            <span class="scope-label">{{ selectedScopeLabel }}</span>
            <v-icon
              v-if="selectedScope"
              size="18"
              class="scope-clear"
              @click.stop="clearScope"
            >mdi-close</v-icon>
            <v-icon v-else size="18" class="scope-caret">mdi-menu-down</v-icon>
          </div>
          <!-- SEARCH INPUT -->
          <v-text-field
            ref="searchInput"
            v-model="q"
            class="search-input"
            :placeholder="searchPlaceholder"
            density="comfortable"
            :variant="searchFieldVariant"
            hide-details
            @keydown.enter.prevent="doSearch"
            @focus="onSearchFocus"
            @blur="onSearchBlur"
          >
            <template #append-inner>
              <div class="cam-container">
                <v-icon size="20" class="cam">mdi-camera-outline</v-icon>
              </div>
              <v-btn icon class="search-btn pl-4" color="#0b63ff" variant="flat" @click="doSearch">
                <span class="search-svg" aria-hidden="true">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" class="ag5_5_0-b2"><path fill="currentColor" d="M17.892 15.064a8 8 0 1 0-2.828 2.828l2.522 2.522a2 2 0 1 0 2.828-2.828zM11 16a5 5 0 1 1 0-10 5 5 0 0 1 0 10"/></svg>
                </span>
              </v-btn>
            </template>
          </v-text-field>
        </div>
        <!-- Suggestion tags panel (absolute, under the input) -->
        <div
          v-if="showSuggestionTags"
          class="suggestion-tags-panel"
          @mousedown.prevent
        >
          <div
            v-for="(tag, idx) in suggestionTags"
            :key="idx"
            class="suggestion-tag"
            @mousedown.prevent="selectSuggestion(tag)"
          >
            {{ tag }}
          </div>
        </div>
      </div>
      <!-- CONTROLS -->
      <div class="controls">
        <!-- LOGIN -->
        <div class="ctrl" @mouseenter="onLoginEnter" @mouseleave="onLeave">
          <v-btn class="ctrl-btn" variant="text" rounded="lg" :ripple="false" @click="onLoginClick">
            <span class="ctrl-icon" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M7.5 14c1.5.005 1.5 1 4.5 1s3-1 4.5-1c1 0 3.5 2.5 3.5 3.5S17.483 21 11.991 21C6.5 21 4 18.5 4 17.5s2.5-3.503 3.5-3.5M12 3C9 3 7 5 7 8s2 5 5 5 5-2 5-5-2-5-5-5"></path></svg>
            </span>
            <div class="ctrl-label">{{ loggedIn ? 'Профиль' : 'Войти' }}</div>
          </v-btn>
        </div>

        <!-- ORDERS -->
        <div class="ctrl">
          <v-btn class="ctrl-btn" variant="text" rounded="lg" :ripple="false">
            <span class="ctrl-icon" aria-hidden="true">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M14.692 5.694c.368-.205.365-.469-.009-.664C13.367 4.343 12.708 4 12 4s-1.367.343-2.683 1.03l-2 1.044c-1.614.842-2.42 1.263-2.869 2.02C4 8.85 4 9.79 4 11.673v1.652c0 1.883 0 2.824.448 3.58s1.255 1.178 2.869 2.02l2 1.044C10.633 20.657 11.292 21 12 21s1.367-.343 2.683-1.03l2-1.044c1.614-.842 2.42-1.263 2.869-2.02.448-.756.448-1.697.448-3.58v-1.652c0-1.883 0-2.824-.448-3.58-.329-.556-.851-.93-1.744-1.423-.367-.203-.389-.204-.763.004L11 10c-.344.19-.739.394-.91.77-.09.197-.09.375-.09.73V14a1 1 0 0 1-2 0v-4a1 1 0 0 1 .514-.874z"></path></svg>
            </span>
            <div class="ctrl-label">Заказы</div>
          </v-btn>
        </div>

        <!-- FAVORITES -->
        <div class="ctrl">
          <v-badge :model-value="favoritesBadge > 0" :content="favoritesBadge" color="#f1117e" offset-x="8" offset-y="6">
            <v-btn class="ctrl-btn" variant="text" rounded="lg" :ripple="false" @click="toFavorites">
              <span class="ctrl-icon" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M3 10.163C3 7.262 5.13 5 8 5c1.929 0 3.244 1.102 4 2.066C12.756 6.102 14.071 5 16 5c2.87 0 5 2.264 5 5.163 0 4.561-4.568 7.856-8.243 9.66a1.71 1.71 0 0 1-1.514 0C7.568 18.02 3 14.724 3 10.163"></path></svg>
              </span>
              <div class="ctrl-label">Избранное</div>
            </v-btn>
          </v-badge>
        </div>

        <!-- BASKET -->
        <div class="ctrl">
          <v-badge :model-value="basketBadge > 0" :content="basketBadge" color="#f1117e" offset-x="8" offset-y="6">
            <v-btn class="ctrl-btn" variant="text" rounded="lg" :ripple="false" @click="toBasket">
              <span class="ctrl-icon" aria-hidden="true">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><path fill="currentColor" d="M9.925 5.371a1 1 0 1 0-1.858-.742L6.317 9h-1.2c-1.076 0-1.614 0-1.913.346-.3.346-.222.878-.067 1.942l.271 1.864c.475 3.265.902 4.898 2.03 5.873s2.778.975 6.08.975h.96c3.302 0 4.953 0 6.08-.975 1.128-.975 1.559-2.608 2.034-5.873l.271-1.864c.155-1.064.233-1.596-.067-1.942S19.96 9 18.883 9h-1.205l-1.75-4.371a1 1 0 0 0-1.857.742L15.523 9h-7.05zM10.997 14v2a1 1 0 0 1-2 0v-2a1 1 0 0 1 2 0M14 13a1 1 0 0 1 1 1v2a1 1 0 0 1-2 0v-2a1 1 0 0 1 1-1"></path></svg>
              </span>
              <div class="ctrl-label">Корзина</div>
            </v-btn>
          </v-badge>
        </div>

        <div v-if="showLoginHint" class="login-hint" @mouseenter="keepHint" @mouseleave="hideHint">
          <div class="text">{{ (loginHint && loginHint.text) || '' }}</div>
          <v-btn class="primary" variant="flat" @click="$emit('open-login')">{{ (loginHint && loginHint.primaryAction && loginHint.primaryAction.caption) || '' }}</v-btn>
          <v-btn class="secondary" variant="text" @click="toProfile">{{ (loginHint && loginHint.secondaryAction && loginHint.secondaryAction.caption) || '' }}</v-btn>
        </div>
      </div>
    </div>
    </div>

    <!-- Category selection overlay -->
    <div v-if="showCategoryPanel" class="category-overlay" @click.self="closeCategoryPanel">
      <div class="category-panel pa-12">
        <v-icon class="close" size="22" @click="closeCategoryPanel">mdi-close</v-icon>
        <div class="cat-item all ml-3 mt-3 mb-6" @click="selectScope(null)">
          <v-icon size="22">mdi-magnify</v-icon>
          <span class="pl-3">Везде</span>
        </div>
        <div class="category-grid">          
          <div
            v-for="opt in scopeWithIcons"
            :key="opt.value"
            class="cat-item"
            @click="selectScope(opt.value)"
          >
            <v-icon size="18">{{ opt.icon }}</v-icon>
            <span>{{ opt.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { shopAssets } from '@/assets/shop-assets.js';
import { mapGetters } from 'vuex';
import { isUnifiedBench } from '@/common/benchTheme';
import { resolveUiVariant } from '@/bench/ui/useBenchUiVariant';
import { textSearchVariantClass, vuetifyFieldVariant } from '@/bench/ui/textSearchStyles';
import { navigateToShopBasket, pushBenchRoute } from '@/common/benchNavigation';
import { getShopBasket, getShopFavoritesCount, getCurrentUsername } from '@/utils/localCache.js';
export default {
  name: 'ShopHeader',
  components: { },
  props: { header: Object, loginHint: Object, loggedIn: Boolean },
  data() { return { q: '', selectedScope: null, showLoginHint: false, hintHover: false, ctrlHover: false, favoritesBadge: 0, basketBadge: 0, showCategoryPanel: false, badgeTimer: null, searchFocused: false, blurTimer: null }; },
  computed: {
    ...mapGetters(['trackConfig']),
    logoSrc() { const img = this.header && this.header.logo && this.header.logo.image; return img ? shopAssets[img] : ''; },
    catalogLabel() { return (this.header && this.header.catalogButton && this.header.catalogButton.label) || 'Каталог'; },
    searchPlaceholder() { return (this.header && this.header.search && this.header.search.placeholder) || 'Искать в каталоге'; },
    searchVariant() {
      return resolveUiVariant(this.trackConfig || {}, 'text_search', 'shop');
    },
    searchFieldVariant() {
      return vuetifyFieldVariant(this.searchVariant);
    },
    searchVariantClass() {
      return textSearchVariantClass(this.searchVariant);
    },
    scopes() { const s = this.header && this.header.search && this.header.search.scopes; return Array.isArray(s) ? s : []; },
    scopeOptions() { return this.scopes.map(v => ({ label: String(v), value: String(v) })); },
    selectedScopeLabel() { return this.selectedScope || 'Везде'; },
    scopeWithIcons() {
      const iconMap = {
        'Электроника': 'mdi-cellphone',
        'Одежда': 'mdi-tshirt-crew-outline',
        'Обувь': 'mdi-shoe-formal',
        'Дом и сад': 'mdi-home-outline',
        'Красота и здоровье': 'mdi-face-man',
        'Спорт и отдых': 'mdi-basketball',
        'Продукты питания': 'mdi-food-apple-outline',
        'Товары для животных': 'mdi-paw-outline',
        'Туризм, рыбалка, охота': 'mdi-tent',
        'Мебель': 'mdi-sofa',
        'Аксессуары': 'mdi-watch-variant',
        'Музыка и видео': 'mdi-music',
        'Товары для взрослых': 'mdi-lock-outline',
        'Цифровые товары': 'mdi-usb',
        'Доставка': 'mdi-leaf',
        'Товары для курения и аксессуары': 'mdi-smoking-off',
        'Билеты, отели, туры': 'mdi-ticket-confirmation-outline'
      };
      return this.scopeOptions.map(o => ({ ...o, icon: iconMap[o.label] || 'mdi-shape-outline' }));
    },
    isCatalogActive() {
      const name = this.$route && this.$route.name;
      return name === 'bench_catalog_catalog' || name === 'bench_catalog_catalog';
    },
    catalogIcon() { return this.isCatalogActive ? 'mdi-close' : 'mdi-view-grid-outline'; },
    suggestionsMap() {
      try {
        const common = this.trackConfig && this.trackConfig.common_elements;
        return (common && common.suggestions_list) || {};
      } catch(e) { return {}; }
    },
    suggestionTags() {
      const q = String(this.q || '').trim().toLowerCase();
      if (!q) return [];
      const keys = Object.keys(this.suggestionsMap || {});
      const ranked = keys
        .map(k => ({ key: k, score: this.fuzzyScore(q, String(k).toLowerCase()) }))
        .filter(it => it.score > 0)
        .sort((a,b) => b.score - a.score)
        .slice(0, 5)
        .map(it => it.key);
      const tags = [];
      ranked.forEach(k => {
        const arr = (this.suggestionsMap[k] && this.suggestionsMap[k].search) || [];
        arr.forEach(s => { const t = String(s); if (t && !tags.includes(t)) tags.push(t); });
      });
      return tags.slice(0, 10);
    },
    showSuggestionTags() { return this.searchFocused && this.suggestionTags.length > 0; }
  },
  methods: {
    // blurSearchInput() {
    //   try {
    //     const el = this.$refs && this.$refs.searchInput && this.$refs.searchInput.$el && this.$refs.searchInput.$el.querySelector('input');
    //     if (el) el.blur();
    //   } catch(e) {}
    //   this.searchFocused = false;
    // },
    goHome() {
      if (this.header && this.header.logo && this.header.logo.to_state && this.header.logo.to_view_type) {
        this.$router.push({ name: this.header.logo.to_view_type, params: { state_id: this.header.logo.to_state, track_id: this.$route.params.track_id } });
      }
    },
    doSearch() {
      const query = { q: this.q };
      if (this.selectedScope) query.scope = this.selectedScope;
      this.$router.push({ name: 'bench_catalog_search', params: { state_id: 'state_search', track_id: this.$route.params.track_id }, query });
      
      this.searchFocused = false;
    },
    onSearchFocus() { this.searchFocused = true; if (this.blurTimer) { clearTimeout(this.blurTimer); this.blurTimer = null; } },
    onSearchBlur() { this.blurTimer = setTimeout(() => { this.searchFocused = false; }, 150); },
    onOverlayClick() { this.searchFocused = false; },
    selectSuggestion(text) {
      const add = (text || '').trim();
      if (!add) return;
      const base = String(this.q || '').trim();
      this.q = base ? `${base} ${add}` : add;
      // keep suggestions open and focus input; do not submit immediately
      this.$nextTick(() => {
        try { const el = this.$refs && this.$refs.searchInput && this.$refs.searchInput.$el && this.$refs.searchInput.$el.querySelector('input'); if (el) el.focus(); } catch(e) {}
      });
    },
    fuzzyScore(query, text) {
      // Simple subsequence-based fuzzy score (higher is better), 0 = no match
      let qi = 0; let score = 0; let streak = 0;
      for (let i = 0; i < text.length && qi < query.length; i++) {
        if (text[i] === query[qi]) { qi++; streak++; score += 2 * streak; }
        else { streak = 0; }
      }
      if (qi < query.length) return 0;
      // Bonus for prefix match
      if (text.startsWith(query)) score += 10;
      // Shorter keys slightly preferred
      return score - Math.max(0, text.length - query.length);
    },
    onLoginClick() {
      if (this.loggedIn) {
        this.$router.push({ name: 'bench_catalog_profile', params: { state_id: 'state_profile', track_id: this.$route.params.track_id } });
      } else {
        this.$emit('open-login');
      }
    },
    onLoginEnter() { if (!this.loggedIn) { this.ctrlHover = true; this.showLoginHint = true; } },
    onLeave() { this.ctrlHover = false; setTimeout(() => { if (!this.hintHover) this.showLoginHint = false; }, 120); },
    keepHint() { this.hintHover = true; },
    hideHint() { this.hintHover = false; this.showLoginHint = false; },
    toProfile() { this.$router.push({ name: 'bench_catalog_profile', params: { state_id: 'state_profile', track_id: this.$route.params.track_id } }); },
    toFavorites() { this.$router.push({ name: 'bench_catalog_favorites', params: { state_id: 'state_favorites', track_id: this.$route.params.track_id } }); },
    toBasket() {
      if (isUnifiedBench(this.trackConfig)) {
        navigateToShopBasket(this.$router, this.$route.params.track_id);
        return;
      }
      pushBenchRoute(this.$router, {
        name: 'bench_catalog_basket',
        stateId: 'state_basket',
        trackId: this.$route.params.track_id,
      });
    },
    onCatalogClick() {
      if (this.isCatalogActive) {
        const backState = (this.header && this.header.catalogButton && this.header.catalogButton.to_state) || 'state_main';
        this.$router.push({ name: 'bench_catalog_main', params: { state_id: backState, track_id: this.$route.params.track_id } });
      } else {
        this.$router.push({ name: 'bench_catalog_catalog', params: { state_id: 'state_catalog', track_id: this.$route.params.track_id } });
      }
    },
    openCategoryPanel() { this.showCategoryPanel = true; },
    closeCategoryPanel() { this.showCategoryPanel = false; },
    selectScope(val) { this.selectedScope = val; this.showCategoryPanel = false; },
    clearScope() { this.selectedScope = null; },
    refreshBadges() {
      try {
        const basketUser = this.loggedIn ? (getCurrentUsername() || 'guest') : 'shop_guest';
        const basketMap = getShopBasket(basketUser) || {};
        this.basketBadge = Object.entries(basketMap).reduce((count, [_, q]) => count + (Number(q) > 0 ? 1 : 0), 0);
        const favUser = getCurrentUsername() || 'guest';
        this.favoritesBadge = getShopFavoritesCount(favUser) || 0;
      } catch(e) { this.favoritesBadge = 0; this.basketBadge = 0; }
    }
  }
  ,
  watch: { loggedIn() { this.refreshBadges(); } },
  mounted() { this.refreshBadges(); this.badgeTimer = setInterval(this.refreshBadges, 500); },
  beforeUnmount() { if (this.badgeTimer) { clearInterval(this.badgeTimer); this.badgeTimer = null; } }
}
</script>

<style src="@/assets/shop.css" scoped></style>
<style scoped>
.bench-market-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.35); z-index: 30; }
.panel { position: relative; }
.search-container {
  z-index: 1000;
  position: relative;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  background-color: white;
  border-radius: 16px;
}
.search-container.search-container-with-tags {
  border: 8px white solid;
}
.search-container-with-tags {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}
.catalog :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.catalog-icon {
  display: inline-flex;
  align-items: center;
}
.catalog-svg {
  color: #f5f7fae6;
}
.search-svg {
  color: #f5f7fae6;
}
.controls .ctrl-btn {
  display: inline-flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  text-transform: none;
  padding: 0px 5px;
  min-width: 54px;
  height: 50px;
  letter-spacing: normal;
}
.controls .ctrl-btn :deep(.v-btn__content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.controls .ctrl-icon { color: #001a3466; }
.controls .ctrl-label { font-size: 12px !important; font-weight: 400 !important; margin-top:-8px; line-height: 1.0; color: #adadad !important; }
.controls .ctrl:first-child .ctrl-label { color: #001a34 !important; font-weight: 600 !important; }
.controls { z-index: 1001; }

/* Search suggestions tag panel */
.search { position: relative; z-index: 1000; }
.suggestion-tags-panel {
  position: absolute;
  left: -8px;
  right: -8px;
  top: 100%;
  background: #ffffff;
  border-top: none;
  z-index: 40;
  padding: 10px 10px 12px 10px;
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.suggestion-tag {
  background: #0030780a;
  color: #001a34;
  border-radius: 10px;
  padding: 6px 10px;
  font-size: 14px;
  cursor: pointer;
  user-select: none;
  font-weight: 600;
}
.suggestion-tag:hover { background: #e9edf2; }
</style>

