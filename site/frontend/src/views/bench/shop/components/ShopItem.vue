<template>
  <div class="card" :data-item-id="itemAttrId" @click="openItemLocal">
    <div class="thumb">
      <div v-if="item && item.original_tag" class="sale-badge">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 2.065c-2-.643-.667 3.71-2 3.71-.667 0-.806-1.258-1.339-1.258C3.994 4.517 2 6.56 2 9.13 2 11.474 3.333 14 6 14c.667 0 1-.212.625-.62-1.875-2.044-1.358-4.042-.63-3.808.94.302 1.823 1.779 2.557-1.35.186-.847.653-.622 1.266 0 .921.932 1.402 2.94-.36 5.157-.291.367.209.621 1.021.621C12.23 14 14 12.106 14 9.13c0-4.004-4-6.423-6-7.065"/>
        </svg>
        Распродажа
      </div>
      <v-img :src="getImage(item && (item.thumbnail || item.img))" cover />
      <button
        type="button"
        class="fav-btn"
        :class="{ active: isFavLocal }"
        :aria-label="isFavLocal ? 'Убрать из избранного' : 'Добавить в избранное'"
        :title="isFavLocal ? 'Убрать из избранного' : 'Добавить в избранное'"
        @click.stop.prevent="toggleFavLocal"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="currentColor" d="M7 5a4 4 0 0 0-4 4c0 3.552 2.218 6.296 4.621 8.22A21.5 21.5 0 0 0 12 19.91a21.6 21.6 0 0 0 4.377-2.69C18.78 15.294 21 12.551 21 9a4 4 0 0 0-4-4c-1.957 0-3.652 1.396-4.02 3.2a1 1 0 0 1-1.96 0C10.652 6.396 8.957 5 7 5m5 17c-.316-.02-.56-.147-.848-.278a23.5 23.5 0 0 1-4.781-2.942C3.777 16.705 1 13.449 1 9a6 6 0 0 1 6-6 6.18 6.18 0 0 1 5 2.568A6.18 6.18 0 0 1 17 3a6 6 0 0 1 6 6c0 4.448-2.78 7.705-5.375 9.78a23.6 23.6 0 0 1-4.78 2.942c-.543.249-.732.278-.845.278"/>
        </svg>
      </button>
    </div>

    <div class="price-row">
      <span class="price">{{ currentPrice }}</span>
      <span v-if="oldPrice" class="old">{{ oldPrice }}</span>
      <span v-if="discountPercent" class="disc">−{{ discountPercent }}%</span>
    </div>
    <div class="name">{{ displayName }}</div>

    <div v-if="item && (item.rating || item.reviews_count)" class="rating-row">
      <div class="rating-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" style="color:#ffb400;"><path fill="currentColor" d="M8 2a1 1 0 0 1 .87.508l1.538 2.723 2.782.537a1 1 0 0 1 .538 1.667L11.711 9.58l.512 3.266A1 1 0 0 1 10.8 13.9L8 12.548 5.2 13.9a1 1 0 0 1-1.423-1.055l.512-3.266-2.017-2.144a1 1 0 0 1 .538-1.667l2.782-.537 1.537-2.723A1 1 0 0 1 8 2"/></svg>
        <span class="rating">{{ item && item.rating }}</span>
      </div>
      <div class="rating-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" style="color:#aaa;"><path fill="currentColor" d="M8.545 13C11.93 13 14 11.102 14 8s-2.07-5-5.455-5C5.161 3 3.091 4.897 3.091 8c0 1.202.31 2.223.889 3.023-.2.335-.42.643-.656.899-.494.539-.494 1.077.494 1.077.89 0 1.652-.15 2.308-.394.703.259 1.514.394 2.42.394"/></svg>
        <span class="reviews">{{ item && item.reviews_count }}</span>
      </div>
      <div v-if="item && item.seller && String(item.seller).toLowerCase() === 'МАРКЕТ'" class="rating-item">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="#005bff"><path d="M8.999 6.994c-.704.196-1.13.728-1.042 1.073.09.345.715.585 1.418.388.704-.196 1.13-.728 1.042-1.073-.09-.345-.714-.585-1.418-.388"/><path d="M14 8c0 3.723-2.277 6-6 6-2.73 0-4.683-1.225-5.53-3.346.261.15.57.214.878.161.855-.146 1.364-1.063 1.058-1.907-.226-.625-.859-1.005-1.492-.896-.38.065-.692.282-.894.578A9 9 0 0 1 2 8c0-3.723 2.277-6 6-6 2.672 0 4.6 1.173 5.475 3.213a.31.31 0 0 0-.291.001.34.34 0 0 0-.158.389l.274 1.065-2.017-.91-.02-.006c-.063-.013-.123.048-.105.118l.566 2.2.011.034a.32.32 0 0 0 .313.22.33.33 0 0 0 .293-.417l-.276-1.074 1.93.87Q14 7.85 14 8M8.834 6.354c-1.019.284-1.686 1.128-1.491 1.885s1.178 1.14 2.197.856 1.687-1.128 1.492-1.885-1.18-1.14-2.198-.856m-2.093.65-1.93.537-.032.011a.337.337 0 0 0-.169.459.32.32 0 0 0 .378.166l.858-.239-.863 2.206-.006.02c-.01.065.048.125.114.107l2.094-.584.034-.012a.34.34 0 0 0 .214-.33c-.014-.216-.21-.354-.4-.301l-1.046.291.862-2.204.006-.02c.011-.066-.048-.126-.114-.108"/><path d="M3.853 9.314c-.065-.494-.557-.789-1-.6a.76.76 0 0 0-.443.798c.064.494.556.79 1 .601a.76.76 0 0 0 .443-.799"/></svg>
        <span style="color: #005bff; font-weight: 600; font-size: 14px;">МАРКЕТ</span>
      </div>
    </div>

    <div v-if="showBasket" class="basket-controls" @click.stop>
      <template v-if="qty > 0">
        <v-btn density="comfortable" icon variant="text" @click="dec"><v-icon>mdi-minus</v-icon></v-btn>
        <div class="qty-value">{{ qty }}</div>
        <v-btn density="comfortable" icon variant="text" @click="inc"><v-icon>mdi-plus</v-icon></v-btn>
      </template>
    </div>
    <div v-if="showBasket && qty === 0" class="basket-controls-add" @click.stop>
      <v-btn class="btn-add" color="#0b63ff" variant="flat" block height="36" @click="addToBasket">
        <template #prepend>
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 16 16" style="color:#f5f7fae6">
            <path fill="currentColor" d="M6.274 2.476a.833.833 0 0 0-1.548-.619L3.27 5.5h-.842c-.897 0-1.345 0-1.594.288S.648 6.52.777 7.407l.226 1.553c.396 2.721.594 4.082 1.533 4.894.94.813 2.314.813 5.064.813h.8c2.75 0 4.125 0 5.064-.813s1.137-2.173 1.533-4.894l.226-1.553c.129-.887.193-1.33-.056-1.619-.25-.288-.697-.288-1.594-.288h-.842l-1.457-3.643a.833.833 0 1 0-1.548.62l1.21 3.023H5.064zm.893 7.19v1.667a.833.833 0 1 1-1.667 0V9.667a.833.833 0 1 1 1.667 0m2.5-.833c.46 0 .833.373.833.834v1.666a.833.833 0 1 1-1.667 0V9.667c0-.46.373-.834.834-.834"></path>
          </svg>
        </template>
        Завтра
      </v-btn>
    </div>
  </div>
  
</template>

<script>
import { defineComponent } from 'vue';
import { getShopBasket, setShopBasketItem, incrementShopBasketItem } from '@/utils/localCache.js';
import { _logActivity } from '@/common/trackHelper';
import { resolveAssetUrl } from '@/common/cdnUrls';

export default defineComponent({
  name: 'ShopItem',
  props: {
    item: { type: Object, required: true },
    getImageSrc: { type: Function, required: false },
    getCurrentPrice: { type: Function, required: false },
    getOldPrice: { type: Function, required: false },
    getDiscountPercent: { type: Function, required: false },
    getDisplayName: { type: Function, required: false },
    getItemKey: { type: Function, required: false },
    isFav: { type: Function, required: false },
    toggleFav: { type: Function, required: false },
    openItem: { type: Function, required: false },
    showBasket: { type: Boolean, default: false },
    loggedIn: { type: Boolean, default: false },
    username: { type: String, default: 'guest' },
    onOpenLogin: { type: Function, required: false }
  },
  data() { return { qty: 0 }; },
  computed: {
    displayName() { return this.getDisplayName ? this.getDisplayName(this.item) : (this.item && (this.item.name || this.item.title || this.item.product_id) || ''); },
    currentPrice() { return this.getCurrentPrice ? this.getCurrentPrice(this.item) : ''; },
    oldPrice() { return this.getOldPrice ? this.getOldPrice(this.item) : ''; },
    discountPercent() { return this.getDiscountPercent ? this.getDiscountPercent(this.item) : ''; },
    isFavLocal() { return this.isFav ? this.isFav(this.item) : false; },
    keyVal() {
      if (this.getItemKey) return this.getItemKey(this.item);
      const it = this.item || {};
      return it.kv_id || it.key || it.id || it.product_id || '';
    },
    itemAttrId() {
      const raw = String(this.keyVal || '');
      if (!raw) return '';
      return raw.startsWith('item_') ? raw : `item_${raw}`;
    },
  },
  methods: {
    getImage(src) {
      if (this.getImageSrc) return this.getImageSrc(src);
      return resolveAssetUrl(src);
    },
    openItemLocal() { if (this.openItem) this.openItem(this.item); },
    toggleFavLocal() { if (this.toggleFav) this.toggleFav(this.item); },
    refreshQty() {
      if (!this.showBasket) return;
      const map = getShopBasket(this.username) || {};
      this.qty = Number(map[`item_${this.keyVal}`] || 0);
    },
    addToBasket() {
      const next = Math.max(1, (this.qty || 0) + 1);
      setShopBasketItem(this.username, `item_${this.keyVal}`, next);
      this.qty = next;
      this.$emit('basket-changed', { key: `item_${this.keyVal}`, qty: next });
      const amount = this.qty;
      _logActivity(this, { type: 'basket_add', item_id: `item_${this.keyVal}`, amount });
    },
    inc() {
      incrementShopBasketItem(this.username, `item_${this.keyVal}`, 1);
      this.refreshQty();
      this.$emit('basket-changed', { key: `item_${this.keyVal}`, qty: this.qty });
      const amount = this.qty;
      _logActivity(this, { type: 'basket_add', item_id: `item_${this.keyVal}`, amount });
    },
    dec() {
      const next = Math.max(0, (this.qty || 0) - 1);
      setShopBasketItem(this.username, `item_${this.keyVal}`, next);
      this.qty = next;
      this.$emit('basket-changed', { key: `item_${this.keyVal}`, qty: next });
      const amount = this.qty;
      _logActivity(this, { type: 'basket_remove', item_id: `item_${this.keyVal}`, amount });
    }
  },
  mounted() { this.refreshQty(); }
});
</script>

<style scoped>
.thumb { position: relative; }
/* v-img fills the thumb and can steal clicks from the favorite control */
.thumb :deep(.v-img),
.thumb :deep(.v-img__img),
.thumb :deep(.v-responsive__content) {
  pointer-events: none;
}
.thumb :deep(.fav-btn) {
  pointer-events: auto;
}
.basket-controls { margin-top: 8px; display: grid; grid-template-columns: 32px 1fr 32px; gap: 6px; align-items: center; }
.basket-controls-add .btn-add { background:#0b63ff !important; color:#fff !important; text-transform:none !important; letter-spacing:normal !important; font-weight:500; border-radius: 8px !important; font-size: 16px !important; padding: 22px 0px !important;}
.basket-controls .qty-value { text-align:center; font-weight:800; }
</style>


