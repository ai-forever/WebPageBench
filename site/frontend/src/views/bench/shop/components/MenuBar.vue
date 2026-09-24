<template>
  <div class="menu-bar-root">
    <div class="menu-bar">
      <div class="container">
      <div class="left">
        <v-btn
          v-for="(item, index) in items"
          :key="index"
          class="menu-item"
          variant="text"
          :style="{ color: colorFor(item) }"
        >
          <span v-if="iconFor(item)" class="menu-icon" aria-hidden="true" v-html="iconFor(item)" />
          <span class="label">{{ item.caption }}</span>
          <span v-if="hasCaret(item)" class="caret" aria-hidden="true" v-html="caretIcon" />
        </v-btn>
      </div>
      <div v-if="loggedIn && (deliveryType || address)" class="right addrbar">
        <button class="addr-type">
          <span class="type">{{ deliveryType || '' }} •</span>
        </button>
        <button class="addr-value">
          <span class="value">{{ address || '' }}</span>
        </button>
      </div>
      
      <div v-if="!loggedIn" class="right addrbar addrbar-container" ref="addrContainer">
        <button class="addr-type">
          <span class="type">Москва •</span>
        </button>
        <button class="addr-value">
          <span class="value">Укажите адрес</span>
        </button>
        <button class="flag-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" class="flag-icon"><rect width="19" height="13" x="2.5" y="5.5" stroke="#001A34" stroke-opacity=".16" opacity=".75" rx="2.5"></rect><path fill="white" d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v2H3z"></path><path fill="#0055CC" d="M3 10h18v4H3z"></path><path fill="#F0121F" d="M3 14h18v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
          <span class="flag-text">RU</span>
        </button>
        <div v-if="showPopup" class="address-popup" :style="popupStyles">
          <div class="popup-arrow"></div>
          <div class="popup-content">
            <div class="popup-title">Добавить адрес в г. Москва?</div>
            <div class="popup-subtitle">Это поможет вам заранее увидеть условия доставки товаров</div>
            <div class="popup-buttons">
              <button class="popup-btn popup-btn-primary" @click="closePopup">Добавить</button>
              <button class="popup-btn popup-btn-secondary" @click="closePopup">Не сейчас</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
    <div v-if="showPopup && !loggedIn" class="popup-backdrop" @click="closePopup"></div>
  </div>
</template>

<script>
import { hasPromptBeenSeen, markPromptSeen } from '@/utils/localCache';

export default {
  name: 'ShopMenuBar',
  props: {
    items: { type: Array, default: () => [] },
    loggedIn: { type: Boolean, default: false },
    deliveryType: { type: String, default: '' },
    address: { type: String, default: '' }
  },
  data() {
    return {
      showPopup: false,
      popupStyles: {}
    };
  },
  mounted() {
    if (!this.loggedIn && !hasPromptBeenSeen('show_shop_address_popup')) {
      this.showPopup = true;
      this.$nextTick(() => {
        this.updatePopupPosition();
      });
    }

    window.addEventListener('resize', this.updatePopupPosition, { passive: true });
    window.addEventListener('scroll', this.updatePopupPosition, { passive: true });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.updatePopupPosition);
    window.removeEventListener('scroll', this.updatePopupPosition);
  },
  computed: {
    caretIcon() {
      return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="uw_i0a"><path fill="currentColor" d="M11.707 6.293a1 1 0 0 1 0 1.414l-3 3a1 1 0 0 1-1.414 0l-3-3a1 1 0 0 1 1.414-1.414L8 8.586l2.293-2.293a1 1 0 0 1 1.414 0"></path></svg>';
    }
  },
  methods: {
    closePopup() {
      this.showPopup = false;
      markPromptSeen('show_shop_address_popup');
    },
    updatePopupPosition() {
      if (!this.showPopup) return;
      const containerEl = this.$refs.addrContainer;
      const popupWidth = 320; // keep in sync with CSS
      if (containerEl && typeof window !== 'undefined') {
        const rect = containerEl.getBoundingClientRect();
        const top = rect.bottom + 12; // space for arrow
        const right = Math.max(0, window.innerWidth - rect.right);
        this.popupStyles = {
          position: 'fixed',
          top: `${top}px`,
          right: `${right}px`,
          width: `${popupWidth}px`,
          maxWidth: '90vw',
          zIndex: 10000
        };
      }
    },
    colorFor(item) {
      const cap = String(item && item.caption || '').toLowerCase();
      if (cap === 'Доставка') return '#00a6a6';
      if (cap === 'Карта') return 'rgba(0, 26, 52, 0.55)';
      if (cap === 'билеты, отели' || cap === 'билеты, отели, туры') return 'rgba(0, 26, 52, 0.55)';
      if (cap === 'для бизнеса') return 'rgba(0, 26, 52, 0.55)';
      return 'rgba(0, 26, 52, 0.55)';
    },
    hasCaret(item) {
      const cap = String(item && item.caption || '').toLowerCase();
      return cap === 'для бизнеса';
    },
    iconFor(item) {
      const cap = String(item && item.caption || '').toLowerCase();
      if (cap === 'Доставка') {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="uw_ah9"><path fill="currentColor" d="M12.159 4.992c-.016-.97-.122-2.408-.826-3.33C10.126.083 7.747-.277 7.295.193s.343 1.796 1.536 3.121c.618.685 1.73 1.727 2.498 2.228.858.56.85.235.833-.38zm-5.698-.829c2.258 0 3.108 1.318 3.74 2.297.372.577.668 1.036 1.132 1.036 1.25 0 3.334.834 3.334 3.03 0 3.22-2.725 5.304-6.154 5.304-3.43 0-7.18-1.667-7.18-6.25 0-2.783 2.052-5.417 5.128-5.417M4.608 9.469a.833.833 0 1 0-1.55-.613c-.475 1.202-.211 2.444.396 3.396.602.945 1.594 1.691 2.73 1.897a.833.833 0 1 0 .298-1.64c-.62-.112-1.236-.545-1.623-1.153-.382-.6-.49-1.282-.25-1.887"></path></svg>';
      }
      if (cap === 'Карта') {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="uw_ah9 uw_ha9"><path fill="currentColor" d="M15.5 8c0 5.833 0 5.833-7.5 5.833S.5 13.833.5 8c0-.417 0-.833.833-.833h13.334c.833 0 .833.416.833.833m-.833-2.5H1.333C.5 5.5.5 5.083.5 4.667c0-2.5 1.667-2.5 7.5-2.5s7.5 0 7.5 2.5c0 .416 0 .833-.833.833"></path></svg>';
      }
      if (cap === 'билеты, отели' || cap === 'билеты, отели, туры') {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="uw_ah9 uw_ha9"><path fill="currentColor" d="M11.753 1.743c.834-.834 2.348-1.816 3.334-.83s0 2.497-.833 3.331c-.617.617-1.212 1.227-1.803 1.832l-.131.134c-.152.22-.193.463-.145.96.117 1.193.241 2.223.359 3.203.107.89.209 1.737.296 2.63.117 1.19.078 1.665-.756 1.664-.766-.001-1-.002-1.166-.42-.331-.833-2.075-4.586-2.075-4.586a47 47 0 0 1-1.939 1.677q-.491.408-.976.821c0 .838 0 2.5-.417 2.5h-.833c-.225 0-.417-.452-.63-.952-.18-.426-.377-.887-.62-1.131-.28-.28-.766-.483-1.198-.662-.476-.199-.887-.37-.887-.588v-1.25c0-.275.741-.183 1.482-.091.37.046.741.091 1.02.091l2.5-2.914S2.583 5.412 1.75 5.078c-.417-.167-.417-.4-.417-1.165 0-.834.477-.872 1.668-.753.892.09 1.74.193 2.63.302.98.12 2.01.246 3.205.365.795.08.94-.073 1.382-.54a50 50 0 0 1 1.099-1.11z"></path></svg>';
      }
      if (cap === 'для бизнеса') {
        return '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="uw_ah9 uw_ha9"><path fill="currentColor" d="M3.11 4.088c.188-1.094.62-1.947 1.327-2.554C5.397.711 6.69.5 8 .5s2.603.211 3.563 1.034c.708.607 1.14 1.46 1.327 2.554 2.238.38 2.61 1.256 2.61 3.079 0 2.279-1.307 3.095-5 3.298-.745.041-.75.008-.836-.463a8 8 0 0 0-.067-.335c-.15-.658-.574-.834-1.597-.834s-1.447.176-1.597.834q-.043.195-.067.335c-.085.47-.091.504-.836.463-3.693-.203-5-1.02-5-3.298 0-1.823.372-2.699 2.61-3.079m1.748-.182A55 55 0 0 1 8 3.833c1.238 0 2.274.021 3.142.073-.157-.535-.396-.878-.663-1.107C9.98 2.372 9.19 2.167 8 2.167s-1.98.205-2.479.632c-.267.23-.506.572-.663 1.107M8 12.167a4.6 4.6 0 0 1-.833-.059c-.39-.074-.582-.244-.768-.41-.211-.188-.417-.371-.899-.405a27 27 0 0 1-1.094-.102c-.814-.09-1.667-.135-2.456-.368-.333-.099-.617-.183-.617.51 0 3.41 1.25 4.167 6.667 4.167s6.667-.758 6.667-4.167c0-.693-.284-.609-.617-.51-.789.233-1.642.278-2.456.368-.345.038-.7.075-1.094.102-.482.034-.688.217-.899.405-.186.166-.377.336-.768.41a4.6 4.6 0 0 1-.833.059"></path></svg>';
      }
      return '';
    }
  }
}
</script>

<style scoped>
.menu-bar .container { display: flex; align-items: center; justify-content: space-between; }
.menu-bar .left { display: flex; align-items: center; gap: 2px; flex-wrap: wrap; }
.menu-item :deep(.v-btn__content) { display: inline-flex; align-items: center; gap: 4px; }
.menu-icon svg { display: inline-block; vertical-align: middle; }
.menu-item .label { white-space: nowrap; }
.menu-item .caret svg { color: #001a3499; }

.addrbar { display: inline-flex; align-items: center; gap: 8px; }
.addrbar .addr-type { color: var(--textTertiary, #6b7280); background: transparent; border: none; cursor: default; }
.addrbar .addr-type .type { font-size: 14px; font-weight: 600; color: #001a3466;}
.addrbar .addr-value { color: var(--textAction, #0b63ff); background: transparent; border: none; cursor: pointer; }
.addrbar .addr-value .value { font-size: 14px; }

.addrbar-container {
  position: relative;
}

.flag-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
}

.flag-icon {
  display: block;
}

.flag-text {
  font-size: 14px;
  font-weight: 500;
  color: #001a34;
}

.popup-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9998;
  background: transparent;
}

.address-popup {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  background: #121212;
  color: white;
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0 8px 24px rgba(0, 26, 52, 0.3);
  z-index: 9999;
  width: 320px;
  max-width: 90vw;
}

.popup-arrow {
  position: absolute;
  top: -8px;
  right: 60px;
  width: 0;
  height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-bottom: 8px solid #121212;
}

.popup-content {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.popup-title {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
  color: white;
}

.popup-subtitle {
  font-size: 14px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.7);
}

.popup-buttons {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.popup-btn {
  flex: 1;
  padding: 5px 10px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.popup-btn-primary {
  background: #005bff;
  color: white;
}

.popup-btn-primary:hover {
  background: #0051e6;
}

.popup-btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.popup-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
