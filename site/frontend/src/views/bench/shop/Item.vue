<template>
  <div v-if="configLoaded" class="bench-market bg-white">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <div class="menu-wrap menu-rounded pb-4">
      <menu-bar
        :items="(common.menu && common.menu.items) || []"
        :logged-in="isLoggedIn"
        :delivery-type="shopUser.delivery_type"
        :address="shopUser.address"
      />
    </div>


    <div class="item-page" v-if="item">
      <div class="top-row">
        <div class="crumbs">
          <span v-for="(bc, bi) in (item.breadcrumbs || [])" :key="'tbc'+bi">
            <span v-if="bi>0" class="sep">›</span>{{ bc.label }}
          </span>
        </div>
        <div class="article">
          <span class="article-links">
            <span class="article-link">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="M1.333 6.333c0-4.117.883-5 5-5 4.118 0 5 .883 5 5 0 4.118-.882 5-5 5-4.117 0-5-.882-5-5"></path><path fill="currentColor" d="M6.333 12.167c-.416 0-.833.416-.833.833 0 1.667 3.249 1.667 4.167 1.667 4.117 0 5-.883 5-5 0-.918 0-4.167-1.667-4.167-.442.035-.833.417-.833.833 0 4.584-1.25 5.834-5.834 5.834"></path></svg>
              <span>Артикул: {{ item && (item.id || '') }}</span>
            </span>
            <span class="article-link-clickable">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="M.5 8C.5 1.824 1.824.5 8 .5s7.5 1.324 7.5 7.5-1.324 7.5-7.5 7.5S.5 14.176.5 8m5.833-4.167h-2.5a.833.833 0 0 0 0 1.667h2.5a.833.833 0 1 0 0-1.667M5.5 10.5H3.833a.833.833 0 0 0 0 1.667H5.5a.833.833 0 0 0 0-1.667m3.333-3.333h-5a.833.833 0 0 0 0 1.666h5a.833.833 0 1 0 0-1.666m2.5 2.5a.833.833 0 1 0-1.666 0v.833h-.834a.833.833 0 0 0 0 1.667h.834V13a.833.833 0 0 0 1.666 0v-.833h.834a.833.833 0 0 0 0-1.667h-.834z"></path></svg>
              <span>В сравнение</span>
            </span>
            <span class="article-link-clickable">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path fill="currentColor" d="M8.833 13.833C8 13.833 8 9.667 8 9.667c-5.833 0-6.25 4.166-6.667 4.166-1.575 0-1.666-9.166 6.667-9.166C8 4.667 8 .5 8.833.5 9.667.5 15.5 5.917 15.5 7.167s-5.833 6.666-6.667 6.666"></path></svg>
              <span>Поделиться</span>
            </span>
          </span>
        </div>
      </div>

      <div class="gallery">
        <div class="gallery-grid">
          <div v-if="gallery.length" class="gallery-thumbs">
            <v-img
              v-for="(g, gi) in gallery"
              :key="'g'+gi"
              :src="getImageSrc(g)"
              height="72"
              cover
              :class="{ 'thumb-active': gi === currentIndex, 'gallery-thumb-img': true }"
              @click="currentIndex = gi"
            />
          </div>
          <v-img :src="getImageSrc(currentImage)" cover class="gallery-main-img" />
        </div>
      </div>

      <div class="info">
        <div class="name-wrap">
          <div ref="nameEl" class="name" :class="{ clamped: !nameExpanded }">{{ displayName }}</div>
          <span v-if="!nameExpanded && nameOverflow" class="name-more" @click="expandName">ещё</span>
        </div>
        <div class="rating-row" v-if="item.rating || item.reviews_count">
          <v-icon size="22" color="#ffb400">mdi-star</v-icon>
          <span class="rating">{{ item.rating }}</span> <span class="rating-separator">•</span>
          <span class="reviews">{{ item.reviews_count }} отзывов</span>
        </div>
        <!-- <div class="chips" v-if="(item.breadcrumbs && item.breadcrumbs.length) || item.brand || item.original_tag">
          <v-chip v-if="item.brand" class="brand" size="small" variant="flat">{{ item.brand }}</v-chip>
          <v-chip v-for="(bc, bi) in (item.breadcrumbs || []).slice(1,4)" :key="'tag'+bi" size="small" variant="flat">{{ bc.label }}</v-chip>
          <v-chip v-if="item.original_tag" class="tag" size="small" variant="flat">{{ item.original_tag }}</v-chip>
        </div> -->

        <!-- Book specific controls -->
        <template v-if="isBook">

          <div class="book-type-row">
            <div class="book-type-label">Тип книги:</div>
            <a href="#" class="book-type-chip" @click.prevent>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" class="book-type-svg">
                <path fill="currentColor" d="M11 5a1 1 0 1 0 0 2h6a1 1 0 1 0 0-2zm0 4a1 1 0 1 0 0 2h4a1 1 0 1 0 0-2z"></path>
                <path fill="currentColor" d="M2 3a3 3 0 0 1 3-3h16a1 1 0 0 1 1 1v22a1 1 0 0 1-1 1H5.5A3.5 3.5 0 0 1 2 20.5zm4 11V2H5a1 1 0 0 0-1 1v14.337A3.5 3.5 0 0 1 5.5 17H20V2H8v12a1 1 0 1 1-2 0m14 5H5.5a1.5 1.5 0 0 0 0 3H20z"></path>
              </svg>
              <span class="book-type-text">Печатная книга</span>
            </a>
          </div>
          <!-- <div style="display:flex; align-items:center; gap:12px; margin: 6px 0 10px;">
            <div style="font-weight:700; color:#001a34;">Тип обложки:</div>
            <v-btn-toggle v-model="coverType" class="cover-toggle" density="comfortable" mandatory>
              <v-btn value="soft" variant="flat">Мягкая обложка</v-btn>
              <v-btn value="hard" variant="flat">Твердый переплет</v-btn>
            </v-btn-toggle>
          </div> -->
        </template>

        <!-- Smartphone specific controls -->
        <template v-else-if="isSmartphone">
          <div class="opt-group" v-if="colorOptions.length">
            <div class="opt-title">Цвет: <span class="opt-value">{{ selectedColorLabel }}</span></div>
            <div class="swatches">
              <div class="swatch-wrap" v-for="c in colorOptions" :key="c.value" :class="{ active: selectedColor === c.value }">
                <button
                  class="swatch"                  
                  :style="{ background: c.hex, borderColor: c.border || '#e5e7eb' }"
                  @click.stop="selectedColor = c.value"
                />
              </div>
            </div>
          </div>
          <div class="opt-group" v-if="storageOptions.length">
            <div class="opt-title">Встроенная память:</div>
            <div class="btns">
              <v-btn
                v-for="s in storageOptions"
                :key="s"
                :variant="selectedStorage === s ? 'flat' : 'outlined'"
                color="#0b63ff"
                size="small"
                class="cap-btn"
                @click.stop="selectedStorage = s"
              >{{ s }} ГБ</v-btn>
            </div>
          </div>
        </template>

        <!-- Pet food specific controls -->
        <template v-else-if="isPetFood">
          <div class="opt-group" v-if="flavorOptions.length">
            <div class="opt-title">Вкус корма для животных:</div>
            <div class="btns">
              <v-btn
                v-for="f in flavorOptions"
                :key="f"
                :variant="selectedFlavor === f ? 'flat' : 'outlined'"
                color="#0b63ff"
                size="small"
                class="cap-btn"
                @click.stop="selectedFlavor = f"
              >{{ f }}</v-btn>
            </div>
          </div>
          <div class="opt-group" v-if="weightOptions.length">
            <div class="opt-title">Вес товара, г:</div>
            <div class="packs">
              <div
                v-for="w in weightOptions"
                :key="w"
                class="pack"
                :class="{ active: selectedWeight === w }"
                @click.stop="selectedWeight = w"
              >
                <div class="pack-discount" v-if="discountPercent">Выгода {{ discountPercent }}%</div>
                <div class="pack-weight">{{ weightLabel(w) }}</div>
                <div class="pack-price">{{ pricePer100gText(w) }}</div>
              </div>
            </div>
          </div>
        </template>

        <!-- General controls for other items -->
        <template v-else>
          <div class="opt-group" v-if="packCountOptions.length">
            <div class="opt-title">Количество в упаковке, шт:</div>
            <div class="packs">
              <div
                v-for="c in packCountOptions"
                :key="c"
                class="pack"
                :class="{ active: selectedPackCount === c }"
                @click.stop="selectedPackCount = c"
              >
                <div class="pack-discount" v-if="discountPercent">Выгода {{ discountPercent }}%</div>
                <div class="pack-weight">{{ c }}</div>
                <div class="pack-price">{{ pricePerUnitText(c) }}</div>
              </div>
            </div>
          </div>
        </template>

        <div class="about" v-if="Object.keys(item.properties || {}).length">
          <div class="about-header">
            <span class="about-title">О товаре</span>
            <!-- <v-btn size="small" variant="text" color="#0b63ff">Перейти к описанию</v-btn> -->
          </div>
          <div class="about-table">
            <div v-for="(val, key, idx) in item.properties" :key="'p'+idx" class="about-row">
              <div class="about-key">{{ key }}</div>
              <div class="about-value">{{ val }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="sidebar">
        <div class="sidebar-sticky">
          <div class="card-panel sidebar-buy sidebar-buy-panel">
            <div class="with-card-price">
              <div class="price-chip">{{ currentPrice }}</div>
              <div class="with-card-note">с МАРКЕТ Картой</div>
            </div>
            <div class="no-card-row">
              <div class="no-card-price no-card-price-nodeco">{{ currentPrice }}</div>
              <div class="no-card-price no-card-price-small">{{ priceBeforeDiscount }}</div>
              <div class="no-card-note">без МАРКЕТ Карты</div>
              <!-- <div v-if="discountPercent" class="disc">-{{ discountPercent }}%</div> -->
            </div>

            <!-- <div class="later-row">
              <v-chip class="later-chip" size="small" variant="flat" color="#6D4AFF" text-color="#ffffff">Оплатить позже</v-chip>
              <div class="later-note">без % до 9 декабря</div>
            </div> -->

            <!-- <div class="want-discount"><v-icon size="18">mdi-checkbox-marked-circle-outline</v-icon><span>Хочу скидку</span></div> -->

            <div v-if="basketQty > 0" class="basket-controls-wrap">
              <div class="basket-controls">
                <button class="in-basket-btn" @click="toBasket">
                  <div class="in-basket-content">
                    <span class="in-basket-big">В корзине</span>
                    <span class="in-basket-small">Перейти</span>
                  </div>
                </button>
                <div class="qty-controls">
                  <button class="qty-btn" @click="dec">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                      <path fill="currentColor" d="M5 11a1 1 0 1 0 0 2h14a1 1 0 1 0 0-2z"></path>
                    </svg>
                  </button>
                  <span class="qty-value">{{ basketQty }}</span>
                  <button class="qty-btn" @click="inc">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                      <path fill="currentColor" d="M12 4a1 1 0 0 0-1 1v6H5a1 1 0 1 0 0 2h6v6a1 1 0 1 0 2 0v-6h6a1 1 0 1 0 0-2h-6V5a1 1 0 0 0-1-1"></path>
                    </svg>
                  </button>
                </div>
                <button class="heart-btn" :class="{ 'heart-active': isFav }" :aria-label="isFav ? 'Убрать из избранного' : 'Добавить в избранное'" @click="toggleFav">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                    <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"></path>
                  </svg>
                </button>
              </div>
              <div class="delivery-label">
                <span>Доставка <b>сегодня</b></span>
              </div>
            </div>

            <div v-else class="add-row" style="display:grid; grid-template-columns: 1fr 56px; gap:8px; margin:12px 0 6px;">
              <div>
                <v-btn class="buy" color="#005bff" variant="flat" block @click="addToBasket">Добавить в корзину</v-btn>
                <div class="delivery mt-2 delivery-note">
                  <span>Доставим <b>завтра</b></span>
                </div>
              </div>
              <div data-widget="webAddToFavorite">
                <button
                  :aria-label="isFav ? 'Убрать из избранного' : 'Добавить в избранное'"
                  class="fav-btn-static"
                  :class="{ 'active': isFav }"
                  @click="toggleFav"
                  :title="isFav ? 'Убрать из избранного' : 'Добавить в избранное'"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                    <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"></path>
                  </svg>
                </button>
              </div>
            </div>

            <!-- <div class="delivery" style="display:flex; align-items:center; gap:8px; margin-top:12px; color:#16a34a;">
              <v-icon size="18">mdi-truck-delivery-outline</v-icon>
              <span>Доставим быстро</span>
            </div> -->
          </div>
          <div class="one-click-wrap">
            <button type="button" class="one-click-btn" @click="buyOneClick">Купить в один клик</button>
          </div>

          <div class="card-panel delivery-panel">
            <h2 class="delivery-title">Доставка и возврат</h2>

            <!-- Address row -->
            <button class="delivery-row delivery-row-clickable">
              <div class="delivery-row-content">
                <div class="delivery-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                    <path fill="currentColor" d="M12 3c-4.5 0-8 3-8 8 0 6 6.5 10 8 10s8-4 8-10c0-5-3.5-8-8-8m0 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6"></path>
                  </svg>
                </div>
                <div class="delivery-text">
                  <div class="delivery-main">{{ userAddress || 'Головинское шоссе, 10Б' }}</div>
                  <div class="delivery-sub">Со склада партнера МАРКЕТ, Jilin Sheng</div>
                </div>
                <div class="delivery-arrow">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                    <path fill="currentColor" d="M5.293 12.293a1 1 0 1 0 1.414 1.414l5-5a1 1 0 0 0 0-1.414l-5-5a1 1 0 0 0-1.414 1.414L9.586 8z"></path>
                  </svg>
                </div>
              </div>
            </button>

            <div class="delivery-divider"></div>

            <!-- Delivery method row -->
            <div class="delivery-row">
              <div class="delivery-text-only">
                <div class="delivery-main">Курьерской службой партнёра</div>
                <div class="delivery-sub">Завтра</div>
              </div>
              <div class="delivery-badge">Без доплат</div>
            </div>

            <div class="delivery-divider"></div>

            <!-- Terms row -->
            <button class="delivery-row delivery-row-clickable">
              <div class="delivery-row-content">
                <div class="delivery-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                    <path fill="currentColor" d="M12 21c5.584 0 9-3.416 9-9s-3.416-9-9-9-9 3.416-9 9 3.416 9 9 9m1-13a1 1 0 1 1-2 0 1 1 0 0 1 2 0m-2 4a1 1 0 1 1 2 0v4a1 1 0 1 1-2 0z"></path>
                  </svg>
                </div>
                <div class="delivery-text">
                  <div class="delivery-main">Условия доставки из-за рубежа</div>
                </div>
                <div class="delivery-arrow">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                    <path fill="currentColor" d="M5.293 12.293a1 1 0 1 0 1.414 1.414l5-5a1 1 0 0 0 0-1.414l-5-5a1 1 0 0 0-1.414 1.414L9.586 8z"></path>
                  </svg>
                </div>
              </div>
            </button>

            <div class="delivery-divider"></div>

            <!-- Return policy row -->
            <button class="delivery-row delivery-row-clickable">
              <div class="delivery-row-content">
                <div class="delivery-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24">
                    <path fill="currentColor" d="M12 21c5.584 0 9-3.416 9-9s-3.416-9-9-9-9 3.416-9 9 3.416 9 9 9m-1.442-4.83c.456.31.58.936.27 1.392a1 1 0 0 1-1.391.264 9 9 0 0 1-.804-.636c-.438-.384-1.008-.95-1.465-1.635a1 1 0 0 1 0-1.11c.457-.686 1.027-1.251 1.465-1.636.256-.225.523-.444.805-.636a1 1 0 0 1 1.125 1.653 6 6 0 0 0-.252.188c.617.006 1.165.01 1.666.002 1.054-.016 1.72-.08 2.16-.22.372-.117.517-.263.622-.487.143-.305.241-.836.241-1.809 0-.964-.095-1.524-.23-1.856-.11-.266-.238-.38-.454-.466-.287-.115-.738-.178-1.5-.194-.433-.009-.896-.002-1.428.005-.414.005-.87.011-1.388.011a1 1 0 1 1 0-2c.45 0 .888-.005 1.304-.01a50 50 0 0 1 1.552-.005c.785.015 1.553.077 2.203.337.722.288 1.249.8 1.562 1.565.286.7.379 1.577.379 2.613 0 1.027-.09 1.934-.43 2.66-.38.807-1.016 1.286-1.831 1.544-.748.236-1.677.296-2.732.311-.49.008-1.046.005-1.658 0q.102.079.209.155"></path>
                  </svg>
                </div>
                <div class="delivery-text">
                  <div class="delivery-main">Можно вернуть в течение 7 дней</div>
                </div>
                <div class="delivery-arrow">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16">
                    <path fill="currentColor" d="M5.293 12.293a1 1 0 1 0 1.414 1.414l5-5a1 1 0 0 0 0-1.414l-5-5a1 1 0 0 0-1.414 1.414L9.586 8z"></path>
                  </svg>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { _logActivity } from '@/common/trackHelper';
import { isUnifiedBench } from '@/common/benchTheme';
import { navigateToShopBasket, pushBenchRoute } from '@/common/benchNavigation';
import { resolveAssetUrl } from '@/common/cdnUrls';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from './components/MenuBar.vue';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import { syncMockLoggedInFromTrack, setCurrentUsername, addShopBasketItem, getShopBasket, setShopBasketItem, incrementShopBasketItem, getShopFavorites, toggleShopFavorite, getCurrentUsername, mergeShopBasket, setShopSelectedItems } from '@/utils/localCache.js';

function toLower(s) { return String(s || '').toLowerCase(); }
function colorNameToHex(name) {
  const n = toLower(name).replace(/[^a-zа-яё]/gi, '');
  const map = {
    'черный': '#000000', 'чёрный': '#000000', 'black': '#000000',
    'белый': '#ffffff', 'white': '#ffffff',
    'зеленый': '#22c55e', 'зелёный': '#22c55e', 'green': '#22c55e',
    'синий': '#2563eb', 'blue': '#2563eb',
    'красный': '#ef4444', 'red': '#ef4444',
    'бежевый': '#e5d5c5', 'beige': '#e5d5c5',
    'розовый': '#f472b6', 'pink': '#f472b6',
    'серый': '#9ca3af', 'серебристый': '#c0c0c0', 'grey': '#9ca3af', 'gray': '#9ca3af'
  };
  return map[n] || '#e5e7eb';
}

export default defineComponent({
  name: 'ShopItem',
  mixins: [benchUserContextMixin],
  components: { SearchBar, ShopLoginDialog, MenuBar },
  data() { return { loggedIn: false, currentIndex: 0, loginDialog: false, coverType: 'soft', basketMap: {}, favoritesKeys: [], nameExpanded: false, nameOverflow: false, selectedColor: null, selectedStorage: null, selectedFlavor: null, selectedWeight: null, selectedPackCount: null, pendingOneClick: false }; },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    content() { const st = this.trackConfig[this.$route.params.state_id]; return st && st.content || {}; },
    username() { return this.benchSessionUser || 'guest'; },
    basketKey() {
      const kv = this.kvStore || {};
      if (kv[this.itemKey]) return this.itemKey;
      const id = this.content && this.content.kv_id;
      return id || this.itemKey || '';
    },
    itemKey() { return this.$route.params.state_id; },
    item() {
      const kv = this.kvStore || {};
      if (kv[this.itemKey]) return kv[this.itemKey];
      const id = this.content && this.content.kv_id;
      return id ? kv[id] : null;
    },
    gallery() { const g = (this.item && this.item.gallery_images) || []; const main = this.item && (this.item.img || this.item.thumbnail); return main ? [main, ...g] : g; },
    currentImage() { return this.gallery[this.currentIndex] || (this.item && (this.item.img || this.item.thumbnail)) || ''; },
    displayName() { return (this.item && (this.item.name || this.item.title || this.item.product_id)) || ''; },
    currentPrice() {
      const it = this.item || {};
      if (it.data_price_raw && it.currency) return `${it.data_price_raw}\u00A0${it.currency}`;
      if (typeof it.data_price === 'number') return this.formatCurrency(it.data_price, it.currency);
      return this.formatCurrency(it.price_with_card || it.price_current || it.price, it.currency);
    },
    oldPrice() { const it = this.item || {}; return it.price_old ? this.formatCurrency(it.price_old, it.currency) : ''; },
    discountPercent() { const it = this.item || {}; if (it.discount_percent) return it.discount_percent; if (it.discount) return String(it.discount).replace('%',''); return ''; },
    basketQty() { const k = this.basketKey; if (!k) return 0; return Number(this.basketMap[k] || 0); },
    isFav() { const k = this.basketKey; if (!k) return false; return this.favoritesKeys.includes(String(k)); },
    priceBeforeDiscount() {
      const it = this.item || {};
      if (it.price_old) return this.formatCurrency(it.price_old, it.currency);
      const percent = Number(this.discountPercent || 0);
      const currentValue = this.getCurrentPriceValue(it);
      if (Number.isFinite(currentValue) && currentValue > 0 && percent > 0 && percent < 100) {
        const base = Math.round(currentValue / (1 - percent / 100));
        return this.formatCurrency(base, it.currency);
      }
      return this.oldPrice || this.currentPrice;
    },
    userAddress() {
      return this.shopUser.address || '';
    },

    // Type detection
    isBook() {
      const name = toLower(this.displayName);
      const bc = (this.item && this.item.breadcrumbs) || [];
      const labels = bc.map(b => toLower(b && b.label));
      const props = Object.keys(this.item && this.item.properties || {}).map(toLower);
      return labels.some(l => /книг/.test(l)) || /книга/.test(name) || props.some(p => /(автор|издатель|страниц)/.test(p));
    },
    isSmartphone() {
      const name = toLower(this.displayName);
      const bc = (this.item && this.item.breadcrumbs) || [];
      const labels = bc.map(b => toLower(b && b.label));
      return labels.some(l => /(смартфон|телефон)/.test(l)) || /(смартфон|iphone|pixel|galaxy|phone)/.test(name);
    },
    isPetFood() {
      const name = toLower(this.displayName);
      const bc = (this.item && this.item.breadcrumbs) || [];
      const labels = bc.map(b => toLower(b && b.label)).join(' ');
      return /корм/.test(name) || /(корм|для животных|кошек|собак|питомц)/.test(labels);
    },

    // Smartphone options with fallbacks
    colorOptions() {
      const it = this.item || {};
      const props = it.properties || {};
      const raw = props['Цвет'] || props['Цвет товара'] || props['Цвета'] || props['Color'] || '';
      let arr = [];
      if (Array.isArray(it.colors)) arr = it.colors;
      else if (typeof raw === 'string') arr = raw.split(/[;,\/\|]/).map(s => s.trim()).filter(Boolean);
      arr = arr.slice(0, 6);
      if (arr.length === 0) arr = ['Черный', 'Белый', 'Зеленый'];
      return arr.map(v => ({ value: String(v), hex: colorNameToHex(v) }));
    },
    selectedColorLabel() { return this.selectedColor || (this.colorOptions[0] && this.colorOptions[0].value) || ''; },
    storageOptions() {
      const it = this.item || {};
      const props = it.properties || {};
      const raw = props['Встроенная память'] || props['Память'] || props['ROM'] || '';
      let nums = [];
      if (Array.isArray(it.storages)) nums = it.storages;
      else if (typeof raw === 'string') {
        const m = raw.match(/(\d+)(?=\s*(гб|gb|гбайт)?)/gi);
        if (m) nums = m.map(x => parseInt(x, 10));
        else nums = raw.split(/[;,\/\|]/).map(s => parseInt(s, 10)).filter(n => Number.isFinite(n));
      }
      if (!nums || nums.length === 0) nums = [128, 256];
      nums = Array.from(new Set(nums.filter(n => Number.isFinite(n)).sort((a,b)=>a-b)));
      return nums.slice(0, 4);
    },

    // Pet food options
    flavorOptions() {
      const it = this.item || {};
      const props = it.properties || {};
      let raw = props['Вкус корма для животных'] || props['Вкус корма'] || props['Вкус'] || '';
      let arr = [];
      if (Array.isArray(it.flavors)) arr = it.flavors;
      else if (typeof raw === 'string') arr = raw.split(/[;,\/\|]/).map(s => s.trim()).filter(Boolean);
      if (arr.length === 0) arr = ['Говядина', 'Курица'];
      return arr.slice(0, 6);
    },
    weightOptions() {
      const it = this.item || {};
      const props = it.properties || {};
      let raw = props['Вес товара, г'] || props['Вес, г'] || props['Вес товара'] || props['Масса нетто'] || '';
      let nums = [];
      if (Array.isArray(it.weights)) nums = it.weights;
      else if (typeof raw === 'string') {
        const parts = raw.split(/[;,\/\|]/).map(s => s.trim()).filter(Boolean);
        nums = parts.map(p => {
          const kg = p.match(/([\d,.]+)\s*кг/i);
          if (kg) { const v = parseFloat(String(kg[1]).replace(',', '.')); return Math.round(v * 1000); }
          const g = p.match(/(\d+)/);
          return g ? parseInt(g[1], 10) : NaN;
        }).filter(n => Number.isFinite(n));
      }
      if (!nums || nums.length === 0) nums = [5000, 13800];
      nums = Array.from(new Set(nums.filter(n => Number.isFinite(n)).sort((a,b)=>a-b)));
      return nums.slice(0, 4);
    },

    // General pack count options
    packCountOptions() {
      const it = this.item || {};
      const props = it.properties || {};
      let raw = props['Количество в упаковке, шт'] || props['Количество в упаковке'] || props['Количество, шт'] || props['Количество предметов'] || props['Кол-во в упаковке'] || '';
      let nums = [];
      if (Array.isArray(it.packCounts)) nums = it.packCounts;
      else if (typeof raw === 'string') nums = raw.split(/[;,\/\|]/).map(s => parseInt(s, 10)).filter(n => Number.isFinite(n));
      if (!nums || nums.length === 0) nums = [8, 12, 24];
      nums = Array.from(new Set(nums.filter(n => Number.isFinite(n)).sort((a,b)=>a-b)));
      return nums.slice(0, 6);
    }
  },
  watch: {
    displayName() { this.nameExpanded = false; this.updateNameOverflow(); },
    colorOptions: { immediate: true, handler(val) { if (val && val.length && !this.selectedColor) this.selectedColor = val[0].value; } },
    storageOptions: { immediate: true, handler(val) { if (val && val.length && (this.selectedStorage == null)) this.selectedStorage = val[0]; } },
    flavorOptions: { immediate: true, handler(val) { if (val && val.length && !this.selectedFlavor) this.selectedFlavor = val[0]; } },
    weightOptions: { immediate: true, handler(val) { if (val && val.length && !this.selectedWeight) this.selectedWeight = val[0]; } },
    packCountOptions: { immediate: true, handler(val) { if (val && val.length && !this.selectedPackCount) this.selectedPackCount = val[0]; } }
  },
  methods: {
    expandName() { this.nameExpanded = true; },
    updateNameOverflow() { this.$nextTick(() => { const el = this.$refs.nameEl; if (!el) { this.nameOverflow = false; return; } this.nameOverflow = el.scrollHeight > el.clientHeight + 1; }); },
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
      try { mergeShopBasket('shop_guest', username, true); } catch(e) {}
      this.refreshBasket();
      this.refreshFavorites();
      if (this.pendingOneClick) {
        this.pendingOneClick = false;
        this.proceedOneClick();
      }
    },
    refreshBasket() { this.basketMap = getShopBasket(this.loggedIn ? this.username : 'shop_guest') || {}; },
    refreshFavorites() { try { this.favoritesKeys = (getShopFavorites(getCurrentUsername()) || []).map(String); } catch(e) { this.favoritesKeys = []; } },
    toggleFav() {
      const k = this.basketKey;
      if (!k) return;
      const wasFav = this.isFav;
      toggleShopFavorite(getCurrentUsername(), String(k));
      this.refreshFavorites();
      const raw = String(k);
      const itemId = raw.startsWith('item_') ? raw : `item_${raw}`;
      _logActivity(this, { type: wasFav ? 'remove_favorites' : 'add_favorites', item_id: itemId });
    },
    addToBasket() {
      if (!this.basketKey) return;
      const user = this.loggedIn ? this.username : 'shop_guest';
      addShopBasketItem(user, this.basketKey, 1);
      this.refreshBasket();
      const amount = this.basketQty;
      _logActivity(this, { type: 'basket_add', item_id: this.basketKey, amount });
    },
    buyOneClick() {
      if (!this.basketKey) return;
      if (!this.loggedIn) {
        this.pendingOneClick = true;
        this.openLoginDialog();
        return;
      }
      this.proceedOneClick();
    },
    proceedOneClick() {
      if (!this.basketKey) return;
      const user = this.username;
      addShopBasketItem(user, this.basketKey, 1);
      setShopSelectedItems(user, { [this.basketKey]: true });
      this.refreshBasket();
      _logActivity(this, { type: 'basket_add', item_id: this.basketKey, amount: this.basketQty });
      pushBenchRoute(this.$router, {
        name: 'bench_catalog_purchase',
        stateId: 'state_purchase',
        trackId: this.$route.params.track_id,
      });
    },
    inc() { if (!this.basketKey) return; const user = this.loggedIn ? this.username : 'shop_guest'; incrementShopBasketItem(user, this.basketKey, 1); this.refreshBasket(); const amount = this.basketQty; _logActivity(this, { type: 'basket_add', item_id: this.basketKey, amount }); },
    dec() { if (!this.basketKey) return; const user = this.loggedIn ? this.username : 'shop_guest'; const cur = Number(this.basketMap[this.basketKey] || 0); const next = Math.max(0, cur - 1); setShopBasketItem(user, this.basketKey, next); this.refreshBasket(); const amount = this.basketQty; _logActivity(this, { type: 'basket_remove', item_id: this.basketKey, amount }); },
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
    getImageSrc(s) { return resolveAssetUrl(s); },
    formatCurrency(value, currencyCode) { const num = Number(value || 0); if (!currencyCode || currencyCode === 'RUB') { const f = num.toLocaleString('ru-RU', { minimumFractionDigits: num % 1 === 0 ? 0 : 2, maximumFractionDigits: 2 }); return `${f}\u00A0₽`; } return `${num.toLocaleString('ru-RU')} ${currencyCode}`.trim(); },
    getCurrentPriceValue(it) { const src = it || this.item || {}; if (typeof src.data_price === 'number') return src.data_price; return Number(src.price_with_card || src.price_current || src.price || 0); },
    weightLabel(w) { return w >= 1000 ? `${(w/1000).toString().replace('.', ',')} кг` : `${w} г`; },
    pricePer100gText(w) { const price = this.getCurrentPriceValue(); const per100 = w > 0 ? price / (w / 100) : 0; const formatted = Math.round(per100); return `${formatted}\u00A0₽/100 г`; },
    pricePerUnitText(n) { const price = this.getCurrentPriceValue(); const per = n > 0 ? price / n : 0; const formatted = Math.round(per); return `${formatted}\u00A0₽/шт`; },
    openOnShop() { const it = this.item || {}; if (it.url) window.open(it.url, '_blank'); },
    getTrackConfig() {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => {
        this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
        const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
        if (kvPath) return this.$store.dispatch(GET_KV_STORE, { kvPath });
        return Promise.resolve();
      }).then(() => { this.refreshBasket(); this.refreshFavorites(); this.updateNameOverflow(); });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
      if (kvPath && (!this.kvStore || !Object.keys(this.kvStore).length)) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.refreshBasket();
          this.refreshFavorites();
          this.updateNameOverflow();
        });
      }
    }
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    this.refreshBasket();
    this.refreshFavorites();
    this.updateNameOverflow();
    window.addEventListener('resize', this.updateNameOverflow);
  },
  beforeUnmount() { window.removeEventListener('resize', this.updateNameOverflow); }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

