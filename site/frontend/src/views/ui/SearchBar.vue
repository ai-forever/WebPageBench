
<template>
  <div class="searchbar">
    <div class="container" :class="{ 'has-catalog': !!additionalButton, 'no-logo': !showLogo && !additionalButton }">
      <v-img
        v-if="showLogo"
        :src="logoSrc"
        class="logo"
        contain
        @click="onLogoClick"
      />
      <div class="search-row">
        <v-btn
          v-if="additionalButton"
          class="catalog-btn"
          variant="flat"
          @click="onAdditionalButtonClick"
        >
          <v-icon size="20">mdi-books</v-icon>
          <span>{{ additionalButton.caption }}</span>
        </v-btn>
        <div class="search-combo" :class="searchVariantClass">
          <v-text-field
            v-model="searchQuery"
            :placeholder="searchPlaceholder"
            density="compact"
            :variant="searchFieldVariant"
            hide-details
            class="search-input"
            @focus="onFocus"
            @blur="onBlur"
            @keydown="onKeyDown"
            @keydown.enter.prevent="onEnter"
            @input="onInput"
          />
          <v-btn class="search-btn" variant="flat" @click="selectSuggestion(searchQuery)">
            {{ searchButtonCaption }}
          </v-btn>
          <div
            v-if="suggestionsVisible && currentSuggestions && currentSuggestions.length"
            class="suggestions-dropdown"
          >
            <div
              v-for="(s, i) in currentSuggestions"
              :key="'sug' + i"
              class="suggestion"
              :class="{ active: i === activeIndex }"
              @mousedown.prevent="selectSuggestion(s)"
            >{{ s }}</div>
          </div>
        </div>
      </div>
      <div class="actions">
        <menu-button
          v-for="(btn, index) in panelButtons"
          :key="index"
          :icon="btn.icon"
          :label="btn.label"
          :button-type="btn.button_type"
          :logged-in="loggedIn"
          :highlight="btn.highlight"
          class="action-btn"
          @click="onPanelButtonClick(btn)"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { assets } from "@/assets/books-assets.js";
import { _logActivity } from "@/common/trackHelper";
import { legacyToBenchViewType } from "@/common/benchViewTypes";
import {
  ensureBenchDomainMerged,
  navigateToBooksBasket,
  navigateToGroceryBasket,
  navigateToShopBasket,
  pushBenchRoute,
  resolveBenchDomain,
} from "@/common/benchNavigation";
import MenuButton from './MenuButton.vue'
import { mapGetters } from 'vuex';
import { resolveUiVariant } from '@/bench/ui/useBenchUiVariant';
import { textSearchVariantClass, vuetifyFieldVariant } from '@/bench/ui/textSearchStyles';
export default {
  components: { MenuButton },
  props: {
    logo: {
      type: [String, Object],
      default: 'logo/logo_ru.svg'
    },
    searchPlaceholder: {
      type: String,
      default: 'Искать книги'
    },
    searchButtonCaption: {
      type: String,
      default: 'Найти'
    },
    panelButtons: {
      type: Array,
      default: () => []
    },
    loggedIn: {
      type: Boolean,
      default: false
    },
    prefillQuery: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      searchQuery: '',
      suggestionsVisible: false,
      activeIndex: -1,
      startSuggestions: [],
      allSuggestions: []
    }
  },
  methods: {
    onAdditionalButtonClick() {
      const btn = this.additionalButton;
      if (!btn) return;
      const to_state = btn.to_state || 'state_main';
      pushBenchRoute(this.$router, {
        name: btn.to_view_type || 'bench_books_main',
        stateId: to_state,
        trackId: this.$route.params.track_id,
      });
    },
    ensureRouteDomainMerged() {
      const routeName = this.$route?.name;
      if (!routeName) return;
      const domain = resolveBenchDomain(legacyToBenchViewType(routeName));
      if (domain) ensureBenchDomainMerged(domain);
    },
    onPanelButtonClick(btn) {
      if (!btn) return;
      this.ensureRouteDomainMerged();

      if (btn.button_type === 'login' && this.loggedIn) {
        const to_state = btn.to_state || 'state_profile';
        const to_view_type = btn.to_view_type || 'bench_books_profile';
        pushBenchRoute(this.$router, {
          name: to_view_type,
          stateId: to_state,
          trackId: this.$route.params.track_id,
        });
        return;
      }
      if (btn.button_type === 'login' && !this.loggedIn) {
        if (btn.dialog) {
          this.$emit(btn.dialog, btn);
          return;
        }
        const routeName = legacyToBenchViewType(this.$route?.name || '');
        const domain = resolveBenchDomain(routeName);
        if (domain === 'grocery') {
          pushBenchRoute(this.$router, {
            name: 'bench_grocery_authorization',
            stateId: 'state_authorization',
            trackId: this.$route.params.track_id,
          });
          return;
        }
      }
      if (btn.dialog) {
        this.$emit(btn.dialog, btn);
        return;
      }
      if (btn.button_type === 'basket') {
        const routeName = legacyToBenchViewType(this.$route?.name || '');
        const domain = resolveBenchDomain(routeName);
        if (domain === 'shop') {
          navigateToShopBasket(this.$router, this.$route.params.track_id);
          return;
        }
        if (domain === 'grocery') {
          navigateToGroceryBasket(this.$router, this.$route.params.track_id);
          return;
        }
        navigateToBooksBasket(this.$router, this.$route.params.track_id);
        return;
      }
      if (!btn.to_view_type) return;
      pushBenchRoute(this.$router, {
        name: btn.to_view_type,
        stateId: btn.to_state,
        trackId: this.$route.params.track_id,
      });
    },
    onLogoClick() {
      if (this.logo && typeof this.logo === 'object' && this.logo.to_state && this.logo.to_view_type) {
        pushBenchRoute(this.$router, {
          name: this.logo.to_view_type,
          stateId: this.logo.to_state,
          trackId: this.$route.params.track_id,
        });
      }
    },
    onFocus() {
      this.suggestionsVisible = true;
    },
    onBlur() {
      // small timeout to allow click
      setTimeout(() => { this.suggestionsVisible = false; }, 150);
    },
    fetchConfigSuggestions() {
      try {
        const cfg = this.$store && this.$store.getters && this.$store.getters.trackConfig;
        const common = cfg && cfg.common_elements && cfg.common_elements.search_bar;
        this.startSuggestions = (common && common.suggestionsStartData) || [];
        this.allSuggestions = (common && common.suggestionsList) || [];
      } catch(e) { this.startSuggestions = []; this.allSuggestions = []; }
    },
    scoredItems(query) {
      const q = String(query || '').trim().toLowerCase();
      if (!q) return this.startSuggestions.slice(0, 10);
      const words = q.split(/\s+/).filter(Boolean);
      const score = (s) => {
        const t = String(s || '').toLowerCase();
        let sc = 0;
        if (t.startsWith(q)) sc += 100; // strong prefix boost
        if (t.includes(q)) sc += 40;
        for (const w of words) {
          if (t.startsWith(w)) sc += 25;
          if (t.includes(w)) sc += 10;
          // simple fuzzy: allow one missing/extra char via subsequence check
          let i = 0; for (const ch of t) { if (ch === w[i]) i++; }
          if (i >= Math.max(1, w.length - 1)) sc += 5;
        }
        // shorter strings slight preference
        sc -= Math.min(20, Math.floor(t.length / 6));
        return sc;
      };
      return this.allSuggestions
        .map(s => ({ s, sc: score(s) }))
        .filter(it => it.sc > 0)
        .sort((a,b) => b.sc - a.sc)
        .slice(0, 10)
        .map(it => it.s);
    },
    onInput() {
      this.suggestionsVisible = true;
      this.activeIndex = -1;
    },
    onKeyDown(e) {
      if (!this.currentSuggestions.length) return;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.activeIndex = (this.activeIndex + 1) % this.currentSuggestions.length;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.activeIndex = (this.activeIndex - 1 + this.currentSuggestions.length) % this.currentSuggestions.length;
      }
    },
    onEnter() {
      const hasActive = this.activeIndex >= 0 && this.currentSuggestions && this.currentSuggestions.length;
      const chosen = hasActive ? this.currentSuggestions[this.activeIndex] : this.searchQuery;
      this.selectSuggestion(chosen);
    },
    selectSuggestion(text) {
      const q = (text || '').trim();
      this.searchQuery = q;
      this.suggestionsVisible = false;
      if (!q) return;
      _logActivity(this, {
        type: "submit_search",
        value: q,
      });
      const routeName = legacyToBenchViewType(this.$route?.name || '');
      const domain = resolveBenchDomain(routeName);
      if (domain === 'grocery') {
        pushBenchRoute(this.$router, {
          name: 'bench_grocery_main',
          stateId: 'state_grocery_main',
          trackId: this.$route.params.track_id,
          query: { q },
        });
        return;
      }
      if (domain === 'shop') {
        pushBenchRoute(this.$router, {
          name: 'bench_catalog_search',
          stateId: 'state_search',
          trackId: this.$route.params.track_id,
          query: { q },
        });
        return;
      }
      pushBenchRoute(this.$router, {
        name: 'bench_books_search',
        stateId: 'state_search',
        trackId: this.$route.params.track_id,
        query: { q },
      });
    }
  },
  computed: {
    ...mapGetters(['trackConfig']),
    searchDomain() {
      const fromRoute = resolveBenchDomain(this.$route?.name);
      return fromRoute || this.trackConfig?.test_data?.active_bench_domain || 'books';
    },
    searchVariant() {
      return resolveUiVariant(this.trackConfig || {}, 'text_search', this.searchDomain);
    },
    searchFieldVariant() {
      return vuetifyFieldVariant(this.searchVariant);
    },
    searchVariantClass() {
      return textSearchVariantClass(this.searchVariant);
    },
    logoSrc() {
      if (!this.logo) return '';
      if (typeof this.logo === 'string') {
        return assets[this.logo];
      }
      if (typeof this.logo === 'object' && this.logo.image) {
        return assets[this.logo.image] || '';
      }
      return '';
    },
    additionalButton() {
      try {
        const cfg = this.$store && this.$store.getters && this.$store.getters.trackConfig;
        return cfg && cfg.common_elements && cfg.common_elements.search_bar && cfg.common_elements.search_bar.additionalButton;
      } catch(e) { return null; }
    },
    showLogo() {
      return !!this.logoSrc && !this.additionalButton;
    },
    currentSuggestions() {
      return this.scoredItems(this.searchQuery);
    },
  }
  ,
  watch: {
    prefillQuery(value) {
      if (value) this.searchQuery = String(value);
    },
    '$route.query.q'(value) {
      if (value != null && value !== '') this.searchQuery = String(value);
    },
  },
  mounted() {
    this.fetchConfigSuggestions();
    if (this.prefillQuery) {
      this.searchQuery = this.prefillQuery;
    } else {
      const q = this.$route && this.$route.query && this.$route.query.q;
      if (q) this.searchQuery = String(q);
    }
  }
}
</script>

<style scoped>
.searchbar .container {
  display: grid;
  grid-template-columns: minmax(0, 1fr) max-content;
  gap: 16px;
  align-items: center;
  max-width: var(--shop-max-width, 1600px);
  margin: 0 auto;
  padding: 12px 16px;
}

.searchbar .container.no-logo,
.searchbar .container.has-catalog {
  grid-template-columns: minmax(0, 1fr) max-content;
  gap: 20px;
}

.searchbar .container:not(.no-logo):not(.has-catalog) {
  grid-template-columns: 160px minmax(0, 1fr) max-content;
}

.searchbar .search-row {
  display: flex;
  align-items: stretch;
  gap: 12px;
  min-width: 0;
}

.searchbar .actions {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  flex-shrink: 0;
}

.searchbar .actions :deep(.action-btn),
.searchbar .actions :deep(.menu-btn) {
  flex-shrink: 0;
}

.suggestions-dropdown {
  position: absolute;
  background: #fff;
  border: 1px solid #d1d5db;
  z-index: 20;
  border-radius: 12px;
  max-height: 360px;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
.suggestion { padding: 12px 16px; cursor: pointer; font-size: 15px; }
.suggestion:hover,
.suggestion.active { background: #f3f4f6; }
</style>