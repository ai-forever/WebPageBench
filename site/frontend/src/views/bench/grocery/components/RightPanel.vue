<template>
  <div class="right-sidebar">
    <div>
      <!-- State 1: Not logged in - Show map -->
      <div v-if="!isLoggedIn" class="map-placeholder">
        <div
          :style="{
            width: '100%',
            height: '100%',
            position: 'relative',
            backgroundImage: `url(${assets.map_image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat'
          }"
        >
          <div class="map-header">
            <h3>{{ mapSection.city }}</h3>
            <p class="map-description">{{ mapSection.description }}</p>
            <v-btn color="#f3345c" class="address-btn">
              {{ mapSection.buttonLabel }}
            </v-btn>
          </div>
        </div>
      </div>

      <!-- State 2: Logged in with empty basket - Show empty basket placeholder -->
      <div v-else-if="isLoggedIn && basketItemCount === 0" class="empty-basket-container">
        <div class="empty-basket-content">
          <div class="empty-basket-header">
            <h3>{{ deliveryAddress }}</h3>
            <p class="delivery-time">Доставка 15 минут</p>
          </div>
          
          <div class="empty-basket-placeholder">
            <svg xmlns="http://www.w3.org/2000/svg" width="150" height="150" fill="none" viewBox="0 0 168 168" style="opacity: 0.4;">
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M99.477 35.632c-2.945-.101-6.12-.176-8.808 1.163a16.33 16.33 0 0 1-14.165 0c-2.667-1.339-5.868-1.264-8.808-1.163l-.048-.304c0-9.395 7.133-17.008 15.936-17.008s15.935 7.613 15.935 17.008"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M73.444 50.17a106 106 0 0 1-1.665-14.261M94.45 49.086a54 54 0 0 1-.983 4.306c-1.093 3.996-5.222 7.751-9.63 7.751-4.406 0-8.535-3.734-9.602-7.751a52 52 0 0 1-.768-3.201M95.903 35.909a114 114 0 0 1-1.446 13.177"></path>
              <path fill="#404040" d="M80.93 42.792a.97.97 0 0 1-.763.704 1.01 1.01 0 0 1-.934-.421c-.49-.662-.453-3.505.902-3.201a1.17 1.17 0 0 1 .79.827c.203.68.203 1.405 0 2.086M88.393 42.792a.97.97 0 0 1-.763.704 1.01 1.01 0 0 1-.934-.421c-.49-.662-.453-3.505.902-3.201a1.17 1.17 0 0 1 .79.827c.203.68.203 1.405 0 2.086"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M73.36 50.202c-3.853 1.238-6.04-3.59-4.871-6.695.613-1.627 2.085-2.134 3.665-1.504M94.65 49.258c3.852 1.237 6.04-3.596 4.871-6.701-.613-1.6-2.086-2.134-3.67-1.5"></path>
              <path fill="#404040" d="m74.723 36.123-2.571 5.863-4.455-6.354"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m74.723 36.123-2.571 5.863-4.455-6.354"></path>
              <path fill="#404040" d="m92.725 36.523 3.126 4.534 3.628-5.425"></path>
              <path fill="#404040" d="m92.725 36.523 3.126 4.534 3.628-5.425"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m92.725 36.523 3.126 4.534 3.628-5.425M75.982 65.3c-4.583 1.29-11.838 2.667-16.005 5.015-3.734 2.134-6.562 5.756-8.477 9.544M108.706 94.882a8.2 8.2 0 0 1-8.2 8.199c-3.772 0-6.962-2.843-8.002-6.402a8.62 8.62 0 0 1 1.798-7.9c2.294-2.465 6.642-2.807 9.688-1.868 3.308 1.025 4.716 4.764 4.716 7.97M108.682 93.046l10.787 25.251M60.625 93.046v56.716M107.08 128.001v22.321"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M38.484 79.608a7.565 7.565 0 0 0-1.328 9.352c1.888 3.415 6.199 4.418 9.736 3.255a7.73 7.73 0 0 0 4.193-3.148c2.043-3.313 1.302-9.896-3.334-11.091.117-2.577.613-5.495.73-8.072.06-1.286.62-4.62-1.008-5.233-3.873-1.457-3.633 5.74-3.782 7.853l-.336 4.732c-.72-2.545-1.297-5.149-2.033-7.581a13.6 13.6 0 0 0-1.366-3.5 1.756 1.756 0 0 0-2.87-.304c-1.248 1.398-.16 4.412.197 5.97l1.692 7.33"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m51.495 82.744-6.877-1.456a3 3 0 0 0-1.6.096 2.02 2.02 0 0 0-1.286 2.72c.576 1.697 2.54 1.89 4.07 2.263 1.948.475 3.922.885 5.901 1.173M37.156 88.96c.032 3.452.059 7.97.086 11.422.032 4.119-.14 8.237 0 12.35.144 3.847.304 8.243 2.134 11.663 2.464 4.662 6.674 7.319 12.1 6.402 4.267-.721 7.116-4.071 9.149-8.318M51.703 87.552v29.822"></path>
              <path fill="#404040" d="m59.625 70.96.934 37.451a72.2 72.2 0 0 0 4.492-22.3c.272-5.895.832-12.185.666-18.096"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m59.625 70.96.934 37.451a72.2 72.2 0 0 0 4.492-22.3c.272-5.895.832-12.185.666-18.096"></path>
              <path fill="#404040" d="m101.896 68.624-2.374 17.808v.048c1.493-.14 3 .006 4.438.432a5.6 5.6 0 0 1 2.134 1.221l-.053-.586 2.214-16.597"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="m101.896 68.624-2.374 17.808v.048c1.493-.14 3 .006 4.438.432a5.6 5.6 0 0 1 2.134 1.221l-.053-.586 2.214-16.597"></path>
              <path fill="#404040" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path>
              <path fill="#404040" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M72.845 23.81c-.064 2.043-.08 4.086-.032 6.13 1.227-2.412 1.969-5.896 2.23-8.59"></path>
              <path fill="#404040" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path>
              <path fill="#404040" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M85.457 19.04a35 35 0 0 1-1.92 8.44h-.214a34.4 34.4 0 0 1-1.92-8.44"></path>
              <path fill="#404040" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59"></path>
              <path fill="#404040" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M93.958 23.276q.102 3.062.038 6.13c-1.227-2.412-1.969-5.895-2.23-8.59M91.902 65.3c4.583 1.29 11.7 2.667 15.856 5.015 5.452 3.11 8.12 8.824 10.136 14.5 2.497 7.026 5.367 13.962 7.57 21.153 1.996 6.514 5.944 14.623 2.332 21.292-2.187 4.033-6.525 7.058-11.241 6.674-5.287-.432-8.733-3.975-10.974-8.536-2.945-5.949-8.077-17.765-10.21-24.061"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.75" d="M75.984 57.164V65.3c2.487 4.561 11.492 6.605 15.92 0l-.028-8.425"></path>
              <path fill="#404040" d="M75.983 65.3c-4.582 1.29-11.838 2.667-16.004 5.015a18.5 18.5 0 0 0-4.322 3.478l-2.87 3.783v-20.38l23.186-.032"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M75.983 65.3c-4.582 1.29-11.838 2.667-16.004 5.015a18.5 18.5 0 0 0-4.322 3.478l-2.87 3.783v-20.38l23.186-.032"></path>
              <path fill="#404040" d="M91.904 65.3c4.583 1.29 11.7 2.667 15.856 5.015a24.1 24.1 0 0 1 5.276 4.177l3.105 5.367-.043-22.695H91.766"></path>
              <path stroke="#404040" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.094" d="M91.904 65.3c4.583 1.29 11.7 2.667 15.856 5.015a24.1 24.1 0 0 1 5.276 4.177l3.105 5.367-.043-22.695H91.766"></path>
            </svg>
            <p class="empty-basket-text">
              Соберите корзину,<br />
              а мы всё быстро привезём
            </p>
          </div>
          
          <div class="empty-basket-footer">
            <v-btn
              color="#b3b3b3"
              class="checkout-btn disabled-btn"
              block
              disabled
            >
              {{ checkoutButtonText }}
            </v-btn>
          </div>
        </div>
      </div>

      <!-- State 3: Logged in with items in basket - Show basket -->
      <div v-else-if="isLoggedIn && basketItemCount > 0" class="basket-container">
        <div class="basket-header">
          <h3 class="basket-address">{{ deliveryAddress }}</h3>
          <p class="delivery-time">Доставка 15 минут</p>
        </div>
        
        <div class="basket-items">
          <div
            v-for="(item, idx) in basketItems"
            :key="idx"
            class="basket-item"
          >
            <div class="basket-item-image">
              <img :src="groceryImageSrc(item)" :alt="item.title" />
            </div>
            <div class="basket-item-info">
              <div class="basket-item-header">
                <div class="basket-item-title">{{ item.title }}</div>
                <div style="width: 30px;">
                </div>
              </div>
              <div class="basket-item-amount">{{ item.amount }}</div>
              <div class="basket-item-footer">
                <div class="basket-item-controls">
                  <div class="basket-control-btn" @click.stop="decrementItem(item.item_id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M0 12a1 1 0 0 1 1-1h22a1 1 0 1 1 0 2H1a1 1 0 0 1-1-1"></path>
                    </svg>
                  </div>
                  <span class="basket-item-quantity">{{ item.quantity }}</span>
                  <div class="basket-control-btn" @click.stop="incrementItem(item.item_id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
                      <g clip-path="url(#clip0_basket)">
                        <path fill="currentColor" d="M12 0a1 1 0 0 1 1 1v8.5a1.5 1.5 0 0 0 1.5 1.5H23a1 1 0 1 1 0 2h-8.5a1.5 1.5 0 0 0-1.5 1.5V23a1 1 0 1 1-2 0v-8.5A1.5 1.5 0 0 0 9.5 13H1a1 1 0 1 1 0-2h8.5A1.5 1.5 0 0 0 11 9.5V1a1 1 0 0 1 1-1"></path>
                      </g>
                      <defs>
                        <clipPath id="clip0_basket">
                          <path fill="#fff" d="M0 0h24v24H0z"></path>
                        </clipPath>
                      </defs>
                    </svg>
                  </div>
                </div>
                <div class="basket-item-prices">
                  <span v-if="item.old_price" class="basket-old-price">{{ Math.round(parseFloat(item.old_price) * item.quantity) }}</span>
                  <span class="basket-item-price">{{ calculateItemTotal(item) }} ₽</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="basket-footer">
          <div class="basket-summary">
            <span class="basket-summary-label">Итого</span>
            <span class="basket-summary-total">{{ basketTotal }} ₽</span>
          </div>
          <v-btn
            :color="isCheckoutEnabled ? 'primary' : '#b3b3b3'"
            :class="['checkout-btn', { 'disabled-btn': !isCheckoutEnabled }]"
            :disabled="!isCheckoutEnabled"
            block
            @click="handleCheckout"
          >
            <div class="checkout-btn-content">
              <span class="checkout-btn-main">{{ checkoutButtonText }}</span>
              <span v-if="checkoutButtonSubtext" class="checkout-btn-sub">{{ checkoutButtonSubtext }}</span>
            </div>
          </v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import { assets } from "@/assets/grocery-assets.js";
import { groceryImageSrc } from "@/common/groceryImages";
import { getGroceryBasket, getGroceryBasketCount, incrementGroceryBasketItem } from "@/utils/localCache.js";

export default defineComponent({
  name: "RightPanel",
  props: {
    isLoggedIn: {
      type: Boolean,
      default: false
    },
    mapSection: {
      type: Object,
      default: () => ({})
    },
    userData: {
      type: Object,
      default: () => ({})
    },
    kvStore: {
      type: Object,
      default: () => ({})
    },
    testData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      assets,
      basket: {},
      refreshKey: 0
    };
  },
  computed: {
    deliveryAddress() {
      return this.userData.address || '';
    },
    minOrderPrice() {
      return this.testData.min_order_price || 850;
    },
    basketItemCount() {
      // Force reactivity by using refreshKey
      this.refreshKey; // eslint-disable-line no-unused-expressions
      return getGroceryBasketCount();
    },
    basketItems() {
      // Force reactivity by using refreshKey
      this.refreshKey; // eslint-disable-line no-unused-expressions
      const basketMap = getGroceryBasket();
      const items = [];
      
      for (const [itemId, quantity] of Object.entries(basketMap)) {
        if (quantity > 0 && this.kvStore[itemId]) {
          const kvItem = this.kvStore[itemId];
          items.push({
            ...kvItem,
            quantity
          });
        }
      }
      
      return items;
    },
    basketTotal() {
      return this.basketItems.reduce((sum, item) => {
        const price = parseFloat(item.price) || 0;
        return sum + (price * item.quantity);
      }, 0);
    },
    remainingAmount() {
      return Math.max(0, this.minOrderPrice - this.basketTotal);
    },
    isCheckoutEnabled() {
      return this.basketTotal >= this.minOrderPrice;
    },
    checkoutButtonText() {
      if (this.basketItemCount === 0) {
        return `Заказ от ${this.minOrderPrice} ₽`;
      }
      
      if (!this.isCheckoutEnabled) {
        return `Заказ от ${this.minOrderPrice} ₽`;
      }
      
      return 'Продолжить';
    },
    checkoutButtonSubtext() {
      if (this.basketItemCount === 0 || this.isCheckoutEnabled) {
        return '';
      }
      return `Не хватает ещё ${this.remainingAmount} ₽`;
    },
    itemsText() {
      const count = this.basketItemCount;
      if (count % 10 === 1 && count % 100 !== 11) return 'товар';
      if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'товара';
      return 'товаров';
    }
  },
  methods: {
    groceryImageSrc,
    calculateItemTotal(item) {
      const price = parseFloat(item.price) || 0;
      return price * item.quantity;
    },
    refreshBasket() {
      this.basket = getGroceryBasket();
      this.refreshKey++;
    },
    incrementItem(itemId) {
      incrementGroceryBasketItem(null, itemId, 1);
      this.refreshBasket();
    },
    decrementItem(itemId) {
      incrementGroceryBasketItem(null, itemId, -1);
      this.refreshBasket();
    },
    handleCheckout() {
      if (this.isCheckoutEnabled) {
        this.$emit('checkout');
      }
    }
  },
  watch: {
    isLoggedIn() {
      // Refresh basket when login state changes
      this.refreshBasket();
    },
    kvStore: {
      deep: true,
      handler() {
        // Refresh when kvStore updates
        this.refreshBasket();
      }
    }
  },
  mounted() {
    this.refreshBasket();
    // Poll for basket changes less frequently to avoid scroll jumping
    this.basketInterval = setInterval(() => {
      const currentBasket = JSON.stringify(getGroceryBasket());
      const previousBasket = JSON.stringify(this.basket);
      // Only refresh if basket actually changed
      if (currentBasket !== previousBasket) {
        this.refreshBasket();
      }
    }, 500);
  },
  beforeUnmount() {
    if (this.basketInterval) {
      clearInterval(this.basketInterval);
    }
  }
});
</script>

<style scoped>
/* Map state styles (existing) */
.map-placeholder {
  flex: 1;
  overflow: hidden;
}

.map-header {
  padding: 10px 24px 15px 24px;
  border-bottom: 1px solid #fff;
  background: #fafafa;
  flex-shrink: 0;
  border-radius: 20px;
}

.map-header h3 {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.address-btn {
  border-radius: 20px;
  text-transform: none;
  font-weight: 600;
  letter-spacing: 0;
  color: white !important;
  padding: 12px 16px !important;
  transition: all 0.2s ease;
  margin-top: 5px;
  box-shadow: none !important;
  width: auto;
  display: inline-flex;
  align-self: flex-start;
}

.address-btn:hover {
  transform: translateY(-1px);
}

.map-description {
  text-indent: 0;
  font-size: 16.5px !important;
  color: #999 !important;
  font-weight: 600;
  line-height: 1.3 !important;
}

/* Empty basket state */
.empty-basket-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 30px;
  overflow: hidden;
}

.empty-basket-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.empty-basket-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f2f2f2;
  background: #fafafa;
  border-radius: 20px 20px 0 0;
}

.empty-basket-header h3 {
  font-size: 22px;
  font-weight: 700;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.delivery-time {
  margin-top: 10px;
  font-size: 18px;
  color: #444;
  font-weight: 600;
  text-indent: 0;
}

.empty-basket-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.empty-basket-placeholder svg {
  margin-bottom: 24px;
}

.empty-basket-text {
  font-size: 18px;
  font-weight: 600;
  color: #b3b3b3;
  text-align: center;
  line-height: 1.4;
  margin: 0;
}

.empty-basket-footer {
  padding: 16px 24px 24px;
  margin-top: auto;
}

/* Basket with items state */
.basket-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 30px;
  overflow: hidden;
}

.basket-header {
  padding: 20px 24px 0 24px;
  background: white;
  border-radius: 20px 20px 0 0;
}

.basket-address {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 4px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.basket-address::after {
  content: '▾';
  font-size: 14px;
  color: #999;
}

.basket-items {
  flex: 1;
  overflow-y: auto;
  padding: 0px 16px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.basket-items::-webkit-scrollbar {
  display: none;
}

.basket-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
}

.basket-item:last-child {
  border-bottom: none;
}

.basket-item-image {
  width: 85px;
  height: 85px;
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

.basket-item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.basket-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.basket-item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 2px;
}

.basket-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #404040;
  line-height: 15px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.basket-item-prices {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;

}

.basket-item-price {
  font-size: 16px;
  font-weight: 600;
  color: #404040;
}

.basket-old-price {
  font-size: 16px;
  font-weight: 500;
  color: #a6a6a6;
  text-decoration: line-through;
}

.basket-item-amount {
  font-size: 13px;
  font-weight: 500;
  color: #a6a6a6;
  margin-bottom: 2px;
}

.basket-item-footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.basket-item-controls {
  display: flex;
  align-items: center;
  gap: 2px;
  background: var(--bench-primary-light, #f2f2f2);
  border-radius: 15px;
  padding: 4px 8px;
  user-select: none;
}

.basket-control-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #222;
}

.basket-control-btn:hover {
  transform: scale(1.15);
}

.basket-control-btn svg {
  width: 14px;
  height: 14px;
}

.basket-item-quantity {
  font-size: 14px;
  font-weight: 600;
  color: #404040;
  min-width: 20px;
  text-align: center;
}
.basket-footer {
  padding: 12px 20px 10px 20px;
  background: white;
}

.basket-summary {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0px;
  margin-bottom: 15px;
}

.basket-summary-label {
  font-size: 13px;
  font-weight: 600;
  color: #999;
}

.basket-summary-total {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.1;
}

.checkout-btn {
  border-radius: 35px;
  text-transform: none;
  font-weight: 600;
  letter-spacing: 0;
  color: white !important;
  font-size: 17px;
  padding: 16px !important;
  height: 56px !important;
  min-height: 56px !important;
  box-shadow: none !important;
  margin-bottom: 12px;
}

.checkout-btn:not(.disabled-btn):hover {
  transform: translateY(-1px);
}

.checkout-btn.disabled-btn {
  opacity: 1 !important;
}

.checkout-btn-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.checkout-btn-main {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.2;
}

.checkout-btn-sub {
  font-size: 16px;
  font-weight: 500;
  line-height: 0.6;
  opacity: 0.85;
}
</style>

