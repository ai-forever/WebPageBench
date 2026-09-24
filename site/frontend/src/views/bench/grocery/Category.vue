<template>
  <div v-if="!pageReady" class="category-loading">
    <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
  </div>
  <div v-else-if="unifiedBench" class="bench-grocery category-view unified-bench">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isUserLoggedIn"
      :prefill-query="searchQuery"
    />
    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div v-if="!dataReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="dataReady">
      <div v-if="searchQuery && searchQuery.length >= 3" class="grid search-grid">
        <h2 class="section-title">Результаты поиска: «{{ searchQuery }}»</h2>
        <div v-if="searchResults.length === 0" class="no-results">
          Ничего не найдено по запросу «{{ searchQuery }}»
        </div>
        <div v-else class="cards grocery-cards">
          <grocery-item
            v-for="(item, iIdx) in searchResults"
            :key="'s' + iIdx"
            :item="item"
            @open="onProductCardClick"
            @basket-changed="loadBasket"
          />
        </div>
      </div>

      <template v-else-if="enrichedCategory">
        <div class="grid category-intro">
          <h1 class="section-title">{{ categoryTitle }}</h1>
          <div v-if="enrichedCategory.tags && enrichedCategory.tags.length" class="tags-section">
            <button
              v-for="(tag, idx) in enrichedCategory.tags"
              :key="idx"
              type="button"
              class="tag-chip"
              :class="{ active: tagFilter === tag }"
              @click="onTagClick(tag)"
            >
              {{ tag }}
            </button>
          </div>
        </div>

        <div
          v-for="(section, sIdx) in visibleCategorySections"
          :key="sIdx"
          class="grid"
          :data-section-idx="sIdx"
        >
          <h2 v-if="section.caption" class="section-title">{{ section.caption }}</h2>
          <div class="cards grocery-cards">
            <grocery-item
              v-for="(item, iIdx) in section.items"
              :key="iIdx"
              :item="item"
              @open="onProductCardClick"
              @basket-changed="loadBasket"
            />
          </div>
        </div>
      </template>
    </div>

    <checkout-drawer
      :is-open="checkoutDrawerOpen"
      :delivery-address="deliveryAddress"
      :bonus-points="bonusPoints"
      :kv-store="kvStore || {}"
      :user-data="userData"
      @close="checkoutDrawerOpen = false"
      @basket-updated="loadBasket"
      @proceed-payment="openSberPayDrawer"
    />

    <sber-pay-drawer
      :is-open="sberpayDrawerOpen"
      :merchant-name="'Доставка'"
      :basket-total="basketTotal"
      :user-short-name="userShortName"
      :card-number="userData.card_number"
      :card-money="userData.card_money"
      @close="sberpayDrawerOpen = false"
    />

    <grocery-product-modal
      v-model="productPreviewOpen"
      :item="previewItem"
      :quantity="previewQuantity"
      :maxed="previewMaxed"
      :recommendations="previewRecommendations"
      @add="incrementItem"
      @remove="decrementItem"
      @select-product="onPreviewSelectProduct"
    />
  </div>

  <div v-else class="bench-grocery category-view">
    <grocery-header
      :header="common.header"
      :user-short-name="userShortName"
      :is-user-logged-in="isUserLoggedIn"
      :search-query="searchQuery"
      @logout="handleLogout"
      @search="handleSearch"
    />

    <div class="main-container">
      <div class="left-sidebar">
        <div class="menu-items">
          <div
            v-for="(item, index) in menuItems"
            :key="index"
            class="menu-item"
          >
            <div class="menu-item-header" @click="toggleMenu(index)">
              <img :src="getAssetImage(item.image)" :alt="item.caption" />
              <span>{{ item.caption }}</span>
            </div>
            <div class="submenu" v-show="isExpanded(index)">
              <div
                v-for="(cat, cIdx) in item.categories || []"
                :key="cIdx"
                class="category-item"
                :class="{ active: cat && cat.id === categoryId }"
                @click="openCategory(cat && cat.id)"
              >
                {{ cat.name }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Center content (scrollable) -->
      <div class="center-content">
        <div class="center-content-wrapper">
          <!-- Search Results (when searching) -->
          <div v-if="searchQuery && searchQuery.length >= 3" class="search-results-section">
            <h2>Результаты поиска: "{{ searchQuery }}"</h2>
            
            <div v-if="searchResults.length === 0" class="no-results">
              Ничего не найдено по запросу "{{ searchQuery }}"
            </div>
            
            <div v-else class="products-grid">
              <div
                v-for="(item, iIdx) in searchResults"
                :key="iIdx"
                class="product-card"
                role="button"
                tabindex="0"
                @click="onProductCardClick(item, $event)"
                @keydown.enter.prevent="onProductCardClick(item, $event)"
              >
                <div class="product-image-container">
                  <div v-if="item.old_price" class="discount-badge">
                    −{{ calculateDiscount(item.price, item.old_price) }}%
                  </div>
                  <img :src="groceryImageSrc(item)" :alt="item.title" loading="lazy" />
                  <div v-if="!hasPrice(item)" class="product-overlay">
                    <span class="overlay-soldout">Больше нет</span>
                  </div>
                  <div v-else-if="getItemQuantity(item.item_id) > 0" class="product-overlay">
                    <div class="overlay-content">
                      <span class="overlay-quantity">{{ getItemQuantity(item.item_id) }}</span>
                      <span v-if="isMaxedOut(item)" class="overlay-soldout">Больше нет</span>
                    </div>
                  </div>
                </div>
                
                <div class="product-info">
                  <div class="product-details">
                    <div class="product-title" :title="item.title">{{ item.title }}</div>
                    <div class="product-amounts">
                      <div v-if="item.amount" class="product-amount">{{ item.amount }}</div>
                      <div v-if="item.badge" class="product-badge">{{ item.badge }}</div>
                    </div>
                  </div>
                  
                  <div v-if="hasPrice(item)" class="product-actions" :class="{ 'in-basket': getItemQuantity(item.item_id) > 0 }">
                    <div v-if="getItemQuantity(item.item_id) > 0" class="action-button decrease-button" @click.stop="decrementItem(item.item_id)">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                        <path fill="currentColor" d="M0 12a1 1 0 0 1 1-1h22a1 1 0 1 1 0 2H1a1 1 0 0 1-1-1"></path>
                      </svg>
                    </div>
                    <div class="price-container">
                      <span v-if="item.old_price && getItemQuantity(item.item_id) === 0" class="old-price">{{ item.old_price }}</span>
                      <span class="current-price">{{ item.price }}&nbsp;₽</span>
                    </div>
                    <div 
                      v-if="!isMaxedOut(item)"
                      class="action-button add-button" 
                      @click.stop="incrementItem(item.item_id)"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                        <g clip-path="url(#clip0_1_902)">
                          <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                        </g>
                        <defs>
                          <clipPath id="clip0_1_902">
                            <path fill="#fff" d="M0 0h24v24H0z"></path>
                          </clipPath>
                        </defs>
                      </svg>
                    </div>
                    <div 
                      v-else
                      class="action-button add-button disabled"
                      aria-disabled="true"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                        <g clip-path="url(#clip0_1_902)">
                          <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                        </g>
                        <defs>
                          <clipPath id="clip0_1_902">
                            <path fill="#fff" d="M0 0h24v24H0z"></path>
                          </clipPath>
                        </defs>
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Normal category content (when not searching) -->
          <div v-else class="category-page">
            <h1 class="category-title">{{ categoryTitle }}</h1>
            
            <!-- Loading skeleton -->
            <div v-if="!dataReady" class="products-loading">
              <div class="products-grid">
                <div v-for="n in 15" :key="n" class="product-skeleton">
                  <v-skeleton-loader type="image" elevation="0"></v-skeleton-loader>
                  <v-skeleton-loader type="article" elevation="0" class="mt-2"></v-skeleton-loader>
                </div>
              </div>
            </div>
            
            <!-- Category content -->
            <div v-if="dataReady && enrichedCategory">
              <!-- Tags section -->
              <div v-if="enrichedCategory.tags && enrichedCategory.tags.length" class="tags-section">
                <button
                  v-for="(tag, idx) in enrichedCategory.tags"
                  :key="idx"
                  type="button"
                  class="tag-chip"
                  :class="{ active: tagFilter === tag }"
                  @click="onTagClick(tag)"
                >
                  {{ tag }}
                </button>
              </div>
              
              <!-- Sections with products -->
              <div
                v-for="(section, sIdx) in visibleCategorySections"
                :key="sIdx"
                class="product-section"
                :data-section-idx="sIdx"
              >
                <h2 v-if="section.caption" class="section-title">{{ section.caption }}</h2>
                
                <div class="products-grid">
                  <div
                    v-for="(item, iIdx) in section.items"
                    :key="iIdx"
                    class="product-card"
                    role="button"
                    tabindex="0"
                    @click="onProductCardClick(item, $event)"
                    @keydown.enter.prevent="onProductCardClick(item, $event)"
                  >
                    <div class="product-image-container">
                      <!-- Discount badge -->
                      <div v-if="item.old_price" class="discount-badge">
                        −{{ calculateDiscount(item.price, item.old_price) }}%
                      </div>
                      <img
                        :src="groceryImageSrc(item)"
                        :alt="item.title"
                        loading="lazy"
                      />
                      <!-- Sold out overlay when no price -->
                      <div v-if="!hasPrice(item)" class="product-overlay">
                        <span class="overlay-soldout">Больше нет</span>
                      </div>
                      <!-- Overlay with quantity when item is in basket -->
                      <div v-else-if="getItemQuantity(item.item_id) > 0" class="product-overlay">
                        <div class="overlay-content">
                          <span class="overlay-quantity">{{ getItemQuantity(item.item_id) }}</span>
                          <span v-if="isMaxedOut(item)" class="overlay-soldout">Больше нет</span>
                        </div>
                      </div>
                    </div>
                    
                    <div class="product-info">
                      <div class="product-details">
                        <div class="product-title" :title="item.title">
                          {{ item.title }}
                        </div>
                        <div class="product-amounts">
                            <div v-if="item.amount" class="product-amount">
                            {{ item.amount }}
                            </div>
                            <div v-if="item.badge" class="product-badge">
                            {{ item.badge }}
                            </div>
                        </div>
                      </div>
                      
                      <div 
                        v-if="hasPrice(item)"
                        class="product-actions"
                        :class="{ 'in-basket': getItemQuantity(item.item_id) > 0 }"
                      >
                        <!-- Decrease button (shown when quantity > 0) -->
                        <div 
                          v-if="getItemQuantity(item.item_id) > 0"
                          class="action-button decrease-button"
                          @click.stop="decrementItem(item.item_id)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M0 12a1 1 0 0 1 1-1h22a1 1 0 1 1 0 2H1a1 1 0 0 1-1-1"></path>
                          </svg>
                        </div>
                        
                        <div class="price-container">
                          <span 
                            v-if="item.old_price && getItemQuantity(item.item_id) === 0" 
                            class="old-price"
                          >
                            {{ item.old_price }}
                          </span>
                          <span class="current-price">{{ item.price }}&nbsp;₽</span>
                        </div>
                        
                        <!-- Add/increase button -->
                        <div 
                          v-if="!isMaxedOut(item)"
                          class="action-button add-button"
                          @click.stop="incrementItem(item.item_id)"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                            <g clip-path="url(#clip0_1_902)">
                              <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                            </g>
                            <defs>
                              <clipPath id="clip0_1_902">
                                <path fill="#fff" d="M0 0h24v24H0z"></path>
                              </clipPath>
                            </defs>
                          </svg>
                        </div>
                        <div 
                          v-else
                          class="action-button add-button disabled"
                          aria-disabled="true"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24">
                            <g clip-path="url(#clip0_1_902)">
                              <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                            </g>
                            <defs>
                              <clipPath id="clip0_1_902">
                                <path fill="#fff" d="M0 0h24v24H0z"></path>
                              </clipPath>
                            </defs>
                          </svg>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Panel -->
      <right-panel
        :is-logged-in="isUserLoggedIn"
        :map-section="common.mapSection || {}"
        :user-data="userData"
        :kv-store="kvStore || {}"
        :test-data="testData"
        @checkout="openCheckoutDrawer"
      />
    </div>

    <checkout-drawer
      :is-open="checkoutDrawerOpen"
      :delivery-address="deliveryAddress"
      :bonus-points="bonusPoints"
      :kv-store="kvStore || {}"
      :user-data="userData"
      @close="checkoutDrawerOpen = false"
      @basket-updated="loadBasket"
      @proceed-payment="openSberPayDrawer"
    />

    <sber-pay-drawer
      :is-open="sberpayDrawerOpen"
      :merchant-name="'Доставка'"
      :basket-total="basketTotal"
      :user-short-name="userShortName"
      :card-number="userData.card_number"
      :card-money="userData.card_money"
      @close="sberpayDrawerOpen = false"
    />

    <grocery-product-modal
      v-model="productPreviewOpen"
      :item="previewItem"
      :quantity="previewQuantity"
      :maxed="previewMaxed"
      :recommendations="previewRecommendations"
      @add="incrementItem"
      @remove="decrementItem"
      @select-product="onPreviewSelectProduct"
    />
  </div>
  
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { DataService } from "@/common/api.service";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";
import { _logActivity } from "@/common/trackHelper";
import { pushBenchRoute, ensureBenchDomainMerged } from "@/common/benchNavigation";
import { isUnifiedBench } from "@/common/benchTheme";
import { applyDefaultMockLoginFromTrackConfig, isGroceryLoggedIn, getGroceryBasket, incrementGroceryBasketItem, getGroceryCurrentUser, syncGrocerySessionFromTrackConfig } from "@/utils/localCache.js";
import { getGroceryUserContext } from "@/common/benchPersonalInfo.js";
import GroceryHeader from "./components/GroceryHeader.vue";
import GroceryProductModal from "./components/GroceryProductModal.vue";
import RightPanel from "./components/RightPanel.vue";
import CheckoutDrawer from "./components/CheckoutDrawer.vue";
import SberPayDrawer from "./components/SberPayDrawer.vue";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import GroceryItem from "./components/GroceryItem.vue";
import { assets } from "@/assets/grocery-assets.js";
import { groceryImageSrc } from "@/common/groceryImages";
import "@/assets/grocery.css";
import "@/assets/books.css";

export default defineComponent({
  name: "GroceryCategory",
  mixins: [StateDelayMixin],
  components: {
    GroceryHeader,
    GroceryProductModal,
    RightPanel,
    CheckoutDrawer,
    SberPayDrawer,
    SearchBar,
    MenuBar,
    GroceryItem,
  },
  data() {
    return {
      assets,
      isUserLoggedIn: false,
      categoryData: null,
      expandedMenu: {},
      dataReady: false,
      basket: {},
      basketRefreshKey: 0,
      searchQuery: '',
      checkoutDrawerOpen: false,
      sberpayDrawerOpen: false,
      productPreviewOpen: false,
      previewItem: null,
      pageReady: false,
      tagFilter: '',
    };
  },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    ready() {
      return !!this.dataReady;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    unifiedBench() {
      return isUnifiedBench(this.trackConfig);
    },
    menuItems() {
      return (this.common.leftMenu && this.common.leftMenu.items) || [];
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    userData() {
      return getGroceryUserContext(this.trackConfig);
    },
    userShortName() {
      return this.userData.shortName || 'Пользователь';
    },
    categoryId() {
      return this.$route.params.state_id;
    },
    categoryTitle() {
      return this.categoryData && this.categoryData.title ? this.categoryData.title : '';
    },
    enrichedCategory() {
      const src = this.categoryData || {};
      const sections = Array.isArray(src.sections) ? src.sections : [];
      const kv = this.kvStore || {};
      const enrichedSections = sections.map(sec => {
        const rawItems = Array.isArray(sec.items) ? sec.items : [];
        const items = rawItems
          .map(id => (typeof id === 'string' ? id : ''))
          .filter(Boolean)
          .map(id => (kv && kv[id] ? kv[id] : null))
          .filter(Boolean);
        return { ...sec, items };
      });
      const hasItems = enrichedSections.some((sec) => sec.items && sec.items.length);
      if (!hasItems) {
        const title = src.title || this.categoryId || 'Подборка';
        return {
          ...src,
          title,
          sections: [{ caption: 'Подборка', items: this.pickItemsForQuery(title, 12) }],
        };
      }
      return { ...src, sections: enrichedSections };
    },
    visibleCategorySections() {
      if (this.tagFilter) {
        return [{ caption: this.tagFilter, items: this.tagSelectionItems }];
      }
      return (this.enrichedCategory && this.enrichedCategory.sections) || [];
    },
    tagSelectionItems() {
      if (!this.tagFilter) return [];
      return this.pickItemsForQuery(this.tagFilter, 12);
    },
    searchResults() {
      if (!this.searchQuery || this.searchQuery.length < 3) return [];
      return this.performSearch(this.searchQuery);
    },
    deliveryAddress() {
      return this.userData.address || '';
    },
    bonusPoints() {
      return this.userData.bonus_points || 0;
    },
    basketTotal() {
      const basketMap = this.basket || {};
      const kv = this.kvStore || {};
      return Object.entries(basketMap).reduce((sum, [itemId, qty]) => {
        const item = kv[itemId];
        if (!item || !qty) return sum;
        const price = parseFloat(item.price) || 0;
        return sum + price * qty;
      }, 0);
    },
    previewQuantity() {
      if (!this.previewItem || !this.previewItem.item_id) return 0;
      return this.getItemQuantity(this.previewItem.item_id);
    },
    previewMaxed() {
      return this.previewItem ? this.isMaxedOut(this.previewItem) : false;
    },
    previewRecommendations() {
      if (!this.previewItem || !this.kvStore) return [];
      const id = this.previewItem.item_id;
      const seen = new Set([id]);
      const out = [];
      if (this.enrichedCategory && this.enrichedCategory.sections) {
        for (const sec of this.enrichedCategory.sections) {
          for (const it of sec.items || []) {
            if (!it || !it.item_id || seen.has(it.item_id)) continue;
            if (!this.hasPrice(it)) continue;
            out.push(it);
            seen.add(it.item_id);
            if (out.length >= 8) return out;
          }
        }
      }
      for (const it of Object.values(this.kvStore)) {
        if (!it || !it.item_id || seen.has(it.item_id)) continue;
        if (!this.hasPrice(it)) continue;
        out.push(it);
        seen.add(it.item_id);
        if (out.length >= 8) break;
      }
      return out;
    },
  },
  methods: {
    groceryImageSrc,
    hasPrice(item) {
      const p = item && item.price;
      return !(p === undefined || p === null || String(p).trim() === "");
    },
    isMaxedOut(item) {
      const max = parseInt(item && item.max_count, 10);
      if (!max || isNaN(max)) return false;
      return this.getItemQuantity(item && item.item_id) >= max;
    },
    handleLogout() { this.isUserLoggedIn = false; },
    checkLoginState() {
      applyDefaultMockLoginFromTrackConfig(this.trackConfig);
      this.isUserLoggedIn = isGroceryLoggedIn();
    },
    getAssetImage(imageName) { return assets[imageName] || ""; },
    calculateDiscount(currentPrice, oldPrice) {
      const current = parseFloat(currentPrice);
      const old = parseFloat(oldPrice);
      if (!old || old === 0) return 0;
      const discount = Math.round(((old - current) / old) * 100);
      return discount > 0 ? discount : 0;
    },
    getItemQuantity(itemId) {
      // Force reactivity by using basketRefreshKey
      this.basketRefreshKey; // eslint-disable-line no-unused-expressions
      return this.basket[itemId] || 0;
    },
    loadBasket() {
      const username = getGroceryCurrentUser() || 'guest';
      this.basket = getGroceryBasket(username);
      this.basketRefreshKey++;
    },
    onProductCardClick(item, e) {
      if (!item) return;
      const t = e && e.target;
      if (t && t.closest && t.closest('.product-actions')) return;
      this.previewItem = item;
      this.productPreviewOpen = true;
    },
    onPreviewSelectProduct(rec) {
      if (!rec) return;
      this.previewItem = rec;
    },
    incrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, 1);
      this.loadBasket();
      const amount = this.getItemQuantity(itemId);
      _logActivity(this, { type: 'basket_add', item_id: itemId, amount });
    },
    decrementItem(itemId) {
      const username = getGroceryCurrentUser() || 'guest';
      incrementGroceryBasketItem(username, itemId, -1);
      this.loadBasket();
      const amount = this.getItemQuantity(itemId);
      _logActivity(this, { type: 'basket_remove', item_id: itemId, amount });
    },
    toggleMenu(index) {
      const isOpen = this.expandedMenu[index];
      this.$set ? this.$set(this.expandedMenu, index, !isOpen) : (this.expandedMenu[index] = !isOpen);
    },
    isExpanded(index) { return !!this.expandedMenu[index]; },
    ensureGroceryDomain() {
      const cfg = this.$store.getters.trackConfig;
      if (isUnifiedBench(cfg)) {
        ensureBenchDomainMerged('grocery');
      }
    },
    expandMenuForCategory() {
      const catId = this.categoryId;
      if (!catId) return;
      const expanded = {};
      this.menuItems.forEach((item, index) => {
        const cats = item.categories || [];
        if (cats.some((c) => c && c.id === catId)) {
          expanded[index] = true;
        }
      });
      this.expandedMenu = expanded;
    },
    async bootstrap() {
      this.ensureGroceryDomain();
      applyDefaultMockLoginFromTrackConfig(this.trackConfig);
      syncGrocerySessionFromTrackConfig(this.trackConfig);
      this.checkLoginState();
      const needConfig = !this.trackConfig || Object.keys(this.trackConfig).length === 0;
      if (needConfig) {
        await this.ensureConfig();
      } else {
        this.ensureGroceryDomain();
        this.applyStateDelay();
      }
      const tasks = [this.fetchKvStoreIfNeeded(), this.fetchCategory()];
      await Promise.all(tasks);
      this.expandMenuForCategory();
      this.dataReady = true;
      this.pageReady = true;
    },
    openCategory(categoryId) {
      if (!categoryId) return;
      this.tagFilter = '';
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_category',
        stateId: String(categoryId),
        trackId: this.$route.params.track_id,
      });
    },
    catalogCategoryIndex() {
      const byName = {};
      const menuBar = (this.common.menu_bar && this.common.menu_bar.items) || [];
      menuBar.forEach((it) => {
        if (it && it.to_state && it.caption) {
          byName[String(it.caption).trim().toLowerCase()] = it.to_state;
        }
      });
      this.menuItems.forEach((block) => {
        (block.categories || []).forEach((cat) => {
          if (cat && cat.id && cat.name) {
            byName[String(cat.name).trim().toLowerCase()] = cat.id;
          }
        });
      });
      return byName;
    },
    findCatalogCategoryId(tag) {
      const key = String(tag || '').trim().toLowerCase();
      if (!key) return null;
      const extra = {
        'комбо-наборы': 'kombo_nabory',
        'аксессуары': 'aksessuary_36',
        'это мне надо': 'eto_mne_nado_2',
        'из других стран': 'iz_drugikh_stran_1',
        'тренажёры, йога и фитнес': 'trenazhyory_yoga_i_fitnes_4',
        'туризм и рыбалка': 'turizm_i_rybalka',
        'вода': 'voda',
        'все виды спорта': 'vse_vidy_sporta',
        'вся готовая еда': 'vsya_gotovaya_eda_13',
        'завезли новое': 'zavezli_novoe',
        'стритфуд': 'stritfud_1',
        'десерты': 'deserty_i_vypechka',
        'напитки': 'napitki_49',
      };
      return this.catalogCategoryIndex()[key] || extra[key] || null;
    },
    hashSeed(text) {
      const s = String(text || '');
      let h = 0;
      for (let i = 0; i < s.length; i += 1) {
        h = ((h << 5) - h) + s.charCodeAt(i);
        h |= 0;
      }
      return Math.abs(h) || 1;
    },
    pickItemsForQuery(query, limit) {
      const kv = this.kvStore || {};
      const cap = Math.max(1, Number(limit) || 12);
      const q = String(query || '').trim().toLowerCase();
      const tokens = q.split(/[\s,./«»\"-]+/).filter((t) => t.length >= 3);
      const scored = [];
      Object.values(kv).forEach((item) => {
        if (!item || !item.title) return;
        const t = String(item.title).toLowerCase();
        let sc = 0;
        if (q && t.includes(q)) sc += 50;
        tokens.forEach((tok) => { if (t.includes(tok)) sc += 12; });
        if (sc > 0) scored.push({ item, sc });
      });
      scored.sort((a, b) => b.sc - a.sc);
      const picked = [];
      const seen = new Set();
      scored.forEach((row) => {
        const id = row.item.item_id || row.item.title;
        if (seen.has(id)) return;
        seen.add(id);
        picked.push(row.item);
      });
      if (picked.length < cap) {
        const pool = Object.values(kv).filter((item) => item && item.title);
        const seed = this.hashSeed(q || this.categoryId);
        for (let i = 0; i < pool.length && picked.length < cap; i += 1) {
          const item = pool[(i * 17 + seed) % pool.length];
          const id = item.item_id || item.title;
          if (seen.has(id)) continue;
          seen.add(id);
          picked.push(item);
        }
      }
      return picked.slice(0, cap);
    },
    onTagClick(tag) {
      if (!tag) return;
      if (this.tagFilter === tag) {
        this.tagFilter = '';
        return;
      }
      const sections = (this.enrichedCategory && this.enrichedCategory.sections) || [];
      const matchIdx = sections.findIndex(
        (sec) => String(sec.caption || '').trim().toLowerCase() === String(tag).trim().toLowerCase(),
      );
      if (matchIdx >= 0 && sections[matchIdx].items && sections[matchIdx].items.length) {
        this.tagFilter = '';
        this.$nextTick(() => {
          const el = this.$el && this.$el.querySelector(`[data-section-idx="${matchIdx}"]`);
          if (el && el.scrollIntoView) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
        return;
      }
      const catId = this.findCatalogCategoryId(tag);
      if (catId && catId !== this.categoryId) {
        this.openCategory(catId);
        return;
      }
      this.tagFilter = tag;
    },
    fetchCategory() {
      this.categoryData = null;
      return DataService.getGroceryCategory({ categoryId: this.categoryId })
        .then((resp) => {
          const payload = resp && resp.data && resp.data.category;
          const parsed = payload ? JSON.parse(payload) : null;
          this.categoryData = parsed;
        })
        .catch(() => { this.categoryData = null; });
    },
    ensureConfig() {
      return this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          this.ensureGroceryDomain();
          this.isUserLoggedIn = isGroceryLoggedIn();
          this.applyStateDelay();
        });
    },
    fetchKvStoreIfNeeded() {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
      if (!kvPath) return Promise.resolve();
      return this.$store.dispatch(GET_KV_STORE, { kvPath });
    },
    handleSearch(query) {
      this.searchQuery = query;
      // Update URL without navigation
      const currentPath = this.$route.path;
      this.$router.replace({ path: currentPath, query: query ? { q: query } : {} });
    },
    performSearch(query) {
      const kv = this.kvStore || {};
      const q = String(query || '').trim().toLowerCase();
      if (!q || q.length < 3) return [];
      
      const words = q.split(/\s+/).filter(Boolean);
      const score = (title) => {
        const t = String(title || '').toLowerCase();
        let sc = 0;
        if (t.startsWith(q)) sc += 100;
        if (t.includes(q)) sc += 40;
        for (const w of words) {
          if (t.startsWith(w)) sc += 25;
          if (t.includes(w)) sc += 10;
          let i = 0; 
          for (const ch of t) { 
            if (ch === w[i]) i++; 
          }
          if (i >= Math.max(1, w.length - 1)) sc += 5;
        }
        sc -= Math.min(20, Math.floor(t.length / 6));
        return sc;
      };
      
      const items = Object.values(kv)
        .filter(item => item && item.title)
        .map(item => ({ item, sc: score(item.title) }))
        .filter(it => it.sc > 0)
        .sort((a, b) => b.sc - a.sc)
        .slice(0, 100)
        .map(it => it.item);
      
      return items;
    },
    openCheckoutDrawer() {
      this.checkoutDrawerOpen = true;
    },
    openSberPayDrawer() {
      this.checkoutDrawerOpen = false;
      setTimeout(() => { this.sberpayDrawerOpen = true; }, 100);
    }
  },
  watch: {
    categoryId(newVal, oldVal) {
      if (newVal && newVal !== oldVal && this.pageReady) {
        this.tagFilter = '';
        this.dataReady = false;
        this.fetchCategory().then(() => {
          this.expandMenuForCategory();
          this.dataReady = true;
        });
      }
    },
    '$route.query.q': {
      handler(newQuery) {
        this.searchQuery = newQuery || '';
      },
      immediate: true,
    }
  },
  mounted() {
    syncGrocerySessionFromTrackConfig(this.trackConfig);
    this.checkLoginState();
    this.loadBasket();
    this.searchQuery = this.$route.query.q || '';
    this.bootstrap();

    this.basketInterval = setInterval(() => {
      const username = getGroceryCurrentUser() || 'guest';
      const currentBasket = JSON.stringify(getGroceryBasket(username));
      const previousBasket = JSON.stringify(this.basket);
      // Only refresh if basket actually changed
      if (currentBasket !== previousBasket) {
        this.loadBasket();
      }
    }, 500);
  },
  activated() {
    syncGrocerySessionFromTrackConfig(this.trackConfig);
    this.checkLoginState();
    this.loadBasket();
  },
  beforeUnmount() {
    if (this.basketInterval) {
      clearInterval(this.basketInterval);
    }
  }
});
</script>

<style scoped>
.category-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 320px;
}

.category-view.bench-grocery.unified-bench {
  --shop-max-width: 1600px;
  height: auto;
  min-height: 100%;
  overflow: visible;
  display: block;
  background: var(--bench-surface, #f0f3f7);
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}

.category-view.bench-grocery.unified-bench .section-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 20px;
  grid-column: 1 / -1;
}

.category-view.bench-grocery.unified-bench .search-grid {
  display: block;
}

.category-view.bench-grocery.unified-bench .grocery-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

.category-view.bench-grocery.unified-bench .tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  grid-column: 1 / -1;
}

.category-view.bench-grocery.unified-bench .tag-chip {
  background: var(--bench-primary-light, #f2f2f2);
  border: none;
  border-radius: 24px;
  padding: 5px 20px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  color: var(--bench-text, #333);
  cursor: pointer;
  transition: all 0.2s ease;
}

.category-view.bench-grocery.unified-bench .tag-chip:hover {
  background: var(--bench-border, #e8e8e8);
}

.category-view.bench-grocery.unified-bench .tag-chip.active {
  background: var(--bench-primary, #4a6fa5);
  color: #fff;
}

@media (max-width: 1400px) {
  .category-view.bench-grocery.unified-bench .grocery-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1100px) {
  .category-view.bench-grocery.unified-bench .grocery-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 800px) {
  .category-view.bench-grocery.unified-bench .grocery-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

.left-sidebar .category-item.active {
  color: var(--grocery-accent, var(--bench-primary, #4a6fa5));
  font-weight: 700;
}

.bench-grocery { --shop-max-width: 1600px; }

/* Search results styles */
.search-results-section {
  padding: 20px 0 32px;
}

.search-results-section h2 {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 24px;
}

.no-results {
  font-size: 18px;
  color: #666;
  text-align: center;
  padding: 40px 20px;
}

/* Category page */
.category-page {
  padding-bottom: 32px;
}

.category-title {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 24px;
}

/* Tags section */
.tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 32px;
}

.tag-chip {
  background: var(--bench-primary-light, #f2f2f2);
  border: none;
  border-radius: 24px;
  padding: 5px 20px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  color: var(--bench-text, #333);
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-chip:hover {
  background: var(--bench-border, #e8e8e8);
}

.tag-chip.active {
  background: var(--bench-primary, #4a6fa5);
  color: #fff;
}

/* Product section */
.product-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 20px;
}

/* Products grid */
.products-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

/* Product card */
.product-card {
  display: block;
  text-decoration: none;
  border-radius: 16px;
  overflow: hidden;
  background: white;
  cursor: pointer;
}

.product-image-container {
  position: relative;
  width: 100%;
  padding-top: 100%;
  overflow: hidden;
  background: #f7f7f7;
  border-radius: 16px;
}

.product-image-container img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(99, 99, 99, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  pointer-events: none;
}

.overlay-quantity {
  font-size: 48px;
  font-weight: 700;
  color: white;
}

.overlay-soldout {
  font-size: 22px;
  font-weight: 700;
  color: white;
}

.overlay-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.discount-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(26, 26, 26, 0.85);
  color: white;
  border-radius: 15px;
  padding: 0px 5px;
  font-size: 14px;
  font-weight: 600;
  z-index: 1;
}

.product-info {
  padding: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.product-details {
  flex: 1;
}

.product-title {
  font-size: 14px;
  font-weight: 600;
  color: #595959;
  line-height: 1.1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}

.product-amount {
  font-size: 13px;
  font-weight: 600;
  color: #a6a6a6;
  display: inline-block;
  line-height: 1;
}

.product-badge {
  font-size: 13px;
  font-weight: 600;
  color: #00b749;
  margin-left: 4px;
  display: inline-block;
  line-height: 1;
}

.product-amounts {
    margin-top: -5px;
}

.product-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--grocery-action-bg, #ffebef);
  border-radius: 20px;
  padding: 6px 8px 6px 12px;
  align-self: flex-start;
  transition: all 0.2s ease;
  user-select: none;
}

.product-actions:hover {
  background: var(--bench-primary-light, #ffe1e7);
}

/* When item is in basket */
.product-actions.in-basket {
  background: var(--grocery-action-active, var(--bench-primary, #4a6fa5));
}

.product-actions.in-basket:hover {
  background: var(--grocery-action-hover, #e62e55);
}

.price-container {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.old-price {
  font-size: 13px;
  font-weight: 600;
  color: #a6a6a6;
  text-decoration: line-through;
}

.current-price {
  font-size: 15px;
  font-weight: 600;
  color: #404040;
}

.product-actions.in-basket .current-price {
  color: white;
}

.action-button {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.action-button:hover {
  transform: scale(1.1);
}

.action-button svg {
  width: 18px;
  height: 18px;
}

.add-button svg {
  color: var(--grocery-accent, var(--bench-primary, #4a6fa5));
}

.product-actions.in-basket .action-button svg {
  color: white;
}

.decrease-button svg {
  color: white;
}

.add-button.disabled {
  cursor: not-allowed;
}

.add-button.disabled svg {
  color: #ffd6df;
}

/* Loading skeleton */
.products-loading {
  margin-top: 24px;
}

.product-skeleton {
  border-radius: 16px;
}

.product-skeleton :deep(.v-skeleton-loader__image) {
  height: 200px;
  border-radius: 16px;
  background: #f7f7f7;
}

.product-skeleton :deep(.v-skeleton-loader__article) {
  background: transparent;
  padding: 0;
}

.product-skeleton :deep(.v-skeleton-loader__text) {
  background: #f7f7f7;
  border-radius: 4px;
  margin-bottom: 6px;
}

.product-skeleton :deep(.v-skeleton-loader) {
  background: transparent;
}

/* Responsive adjustments */
@media (max-width: 1400px) {
  .products-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 1100px) {
  .products-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 800px) {
  .products-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>

