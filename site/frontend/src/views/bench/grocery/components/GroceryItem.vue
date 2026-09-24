<template>
  <div
    class="grocery-card card"
    role="button"
    tabindex="0"
    :data-item-id="itemId"
    @click="onCardClick"
    @keydown.enter.prevent="onCardClick"
  >
    <div class="thumb image-wrap">
      <div v-if="discountPercent" class="discount-badge">−{{ discountPercent }}%</div>
      <img :src="thumbSrc" :alt="item.title" loading="lazy" />
      <div v-if="!hasPrice" class="product-overlay">
        <span class="overlay-soldout">Больше нет</span>
      </div>
      <div v-else-if="qty > 0" class="product-overlay">
        <div class="overlay-content">
          <span class="overlay-quantity">{{ qty }}</span>
          <span v-if="maxed" class="overlay-soldout">Больше нет</span>
        </div>
      </div>
    </div>

    <div class="product-info">
      <div class="product-title" :title="item.title">{{ item.title }}</div>
      <div v-if="item.amount || item.badge" class="product-amounts">
        <span v-if="item.amount" class="product-amount">{{ item.amount }}</span>
        <span v-if="item.badge" class="product-badge">{{ item.badge }}</span>
      </div>

      <div
        v-if="hasPrice"
        class="product-actions"
        :class="{ 'in-basket': qty > 0 }"
        @click.stop
      >
        <button
          v-if="qty > 0"
          type="button"
          class="action-button decrease-button"
          aria-label="Убрать"
          @click="decrement"
        >
          <v-icon size="18">mdi-minus</v-icon>
        </button>
        <div class="price-container">
          <span v-if="item.old_price && qty === 0" class="old-price">{{ item.old_price }}</span>
          <span class="current-price">{{ item.price }}&nbsp;₽</span>
        </div>
        <button
          v-if="!maxed"
          type="button"
          class="action-button add-button"
          aria-label="Добавить"
          @click="increment"
        >
          <v-icon size="18">mdi-plus</v-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import {
  getGroceryBasket,
  getGroceryCurrentUser,
  incrementGroceryBasketItem,
} from '@/utils/localCache.js';
import { _logActivity } from '@/common/trackHelper';
import { groceryImageSrc } from '@/common/groceryImages';

export default defineComponent({
  name: 'GroceryItem',
  props: {
    item: { type: Object, required: true },
  },
  emits: ['open', 'basket-changed'],
  data() {
    return { qty: 0 };
  },
  computed: {
    itemId() {
      return (this.item && this.item.item_id) || '';
    },
    thumbSrc() {
      return groceryImageSrc(this.item);
    },
    hasPrice() {
      const p = this.item && this.item.price;
      return !(p === undefined || p === null || String(p).trim() === '');
    },
    maxed() {
      const max = parseInt(this.item && this.item.max_count, 10);
      if (!max || Number.isNaN(max)) return false;
      return this.qty >= max;
    },
    discountPercent() {
      const current = parseFloat(this.item && this.item.price);
      const old = parseFloat(this.item && this.item.old_price);
      if (!old || old === 0 || Number.isNaN(current)) return 0;
      const discount = Math.round(((old - current) / old) * 100);
      return discount > 0 ? discount : 0;
    },
  },
  mounted() {
    this.refreshQty();
  },
  methods: {
    username() {
      return getGroceryCurrentUser() || 'guest';
    },
    refreshQty() {
      const basket = getGroceryBasket(this.username()) || {};
      this.qty = Number(basket[this.itemId] || 0);
    },
    increment() {
      if (!this.itemId) return;
      incrementGroceryBasketItem(this.username(), this.itemId, 1);
      this.refreshQty();
      const amount = this.qty;
      _logActivity(this, { type: 'basket_add', item_id: this.itemId, amount });
      this.$emit('basket-changed', { itemId: this.itemId, qty: amount });
    },
    decrement() {
      if (!this.itemId) return;
      incrementGroceryBasketItem(this.username(), this.itemId, -1);
      this.refreshQty();
      const amount = this.qty;
      _logActivity(this, { type: 'basket_remove', item_id: this.itemId, amount });
      this.$emit('basket-changed', { itemId: this.itemId, qty: amount });
    },
    onCardClick(e) {
      const t = e && e.target;
      if (t && t.closest && t.closest('.product-actions')) return;
      this.$emit('open', this.item);
    },
  },
});
</script>

<style scoped>
.grocery-card {
  display: block;
  text-decoration: none;
  border-radius: 16px;
  overflow: hidden;
  background: white;
  cursor: pointer;
}

.thumb {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: #f7f7f7;
  border-radius: 16px;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-overlay {
  position: absolute;
  inset: 0;
  background: rgba(99, 99, 99, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  pointer-events: none;
}

.overlay-quantity {
  font-size: 40px;
  font-weight: 700;
  color: white;
}

.overlay-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.overlay-soldout {
  font-size: 18px;
  font-weight: 700;
  color: white;
}

.discount-badge {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background: rgba(26, 26, 26, 0.85);
  color: white;
  border-radius: 15px;
  padding: 0 5px;
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
}

.product-amount {
  font-size: 13px;
  font-weight: 600;
  color: #a6a6a6;
}

.product-badge {
  font-size: 13px;
  font-weight: 600;
  color: #00b749;
  margin-left: 4px;
}

.product-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--grocery-action-bg, #ffebef);
  border-radius: 20px;
  padding: 6px 8px 6px 12px;
  align-self: flex-start;
}

.product-actions.in-basket {
  background: var(--grocery-action-active, var(--bench-primary, #4a6fa5));
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

.product-actions.in-basket .current-price,
.product-actions.in-basket .action-button {
  color: white;
}

.action-button {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  cursor: pointer;
  padding: 0;
}

.add-button {
  color: var(--grocery-accent, var(--bench-primary, #4a6fa5));
}

.decrease-button {
  color: white;
}
</style>
