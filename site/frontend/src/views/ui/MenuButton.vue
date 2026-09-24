<template>
  <div
    class="menu-btn"
    :class="{ highlight: highlight }"
    role="button"
    tabindex="0"
    @click="handleClick"
    @keydown.enter.prevent="handleClick"
    @keydown.space.prevent="handleClick"
  >
    <v-badge :model-value="showBasketBadge" :content="basketCount" color="#ff6d00" offset-x="8" offset-y="6">
      <v-btn class="btn" :variant="variant" :rounded="rounded" :ripple="false" tabindex="-1">
        <v-icon v-if="actionIcon" size="20">{{ actionIcon }}</v-icon>
        <div class="label">{{ actionLabel }}</div>
      </v-btn>
    </v-badge>
  </div>
</template>

<script>
import {
  getBasketItems,
  getCurrentUsername,
  getGroceryBasketCount,
  getGroceryCurrentUser,
  getShopBasket,
} from "@/utils/localCache.js";
import { legacyToBenchViewType } from "@/common/benchViewTypes";
import { resolveBenchDomain } from "@/common/benchNavigation";
export default {
  props: {
    icon: {
      type: String,
      default: ''
    },
    label: {
      type: String,
      required: true
    },
    badge: {
      type: [Number, String],
      default: null
    },
    buttonType: {
      type: String,
      default: ''
    },
    loggedIn: {
      type: Boolean,
      default: false
    },
    highlight: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      basketCount: 0,
      basketTimer: null
    };
  },
  computed: {
    actionIcon() {
      return this.icon;
    },
    actionLabel() {
      if (this.loggedIn && this.buttonType === 'login') {
        return 'Профиль';
      }
      return this.label;
    },
    variant() {
      return 'text';
    },
    rounded() {
      return 'lg';
    },
    isBasketButton() {
      return this.buttonType === 'basket';
    },
    showBasketBadge() {
      if (this.badge != null && this.badge !== '') return true;
      return this.isBasketButton && this.basketCount > 0;
    }
  },
  watch: {
    loggedIn() {
      this.updateBasketCount();
    }
  },
  methods: {
    handleClick() {
      this.$emit('click');
    },
    updateBasketCount() {
      try {
        const domain = resolveBenchDomain(legacyToBenchViewType(this.$route?.name || ''));
        if (domain === 'grocery') {
          const user = getGroceryCurrentUser() || 'guest';
          this.basketCount = getGroceryBasketCount(user);
          return;
        }
        if (domain === 'shop') {
          const user = this.loggedIn ? (getCurrentUsername() || 'guest') : 'shop_guest';
          const map = getShopBasket(user) || {};
          this.basketCount = Object.values(map).reduce(
            (count, q) => count + (Number(q) > 0 ? 1 : 0),
            0,
          );
          return;
        }
        const user = this.loggedIn ? (getCurrentUsername() || 'guest') : 'guest';
        const items = getBasketItems(user);
        this.basketCount = Array.isArray(items) ? items.length : 0;
      } catch (e) {
        this.basketCount = 0;
      }
    }
  },
  mounted() {
    this.updateBasketCount();
    this.basketTimer = setInterval(this.updateBasketCount, 500);
  },
  beforeUnmount() {
    if (this.basketTimer) {
      clearInterval(this.basketTimer);
      this.basketTimer = null;
    }
  }
}
</script>

<style scoped>
.menu-btn .btn {
  display: inline-flex;
  align-items: center;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  text-transform: none;
  padding: 2px 2px;
  min-width: 54px;
  height: 56px;
  font-weight: 800;
  color: var(--bench-text, #212121);
  pointer-events: none;
}
.menu-btn .btn :deep(.v-btn__content) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.menu-btn .label { font-size: 12px; line-height: 1; }
.menu-btn.highlight  { color: #f1edff; border-radius: 14px; padding: 6px; }
.menu-btn { cursor: pointer; position: relative; z-index: 1; }
.menu-btn :deep(.v-badge__wrapper),
.menu-btn :deep(.v-badge__badge) {
  pointer-events: none;
}
</style>


