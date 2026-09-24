<template>
  <v-dialog
    :model-value="modelValue"
    max-width="960"
    class="grocery-pm-dialog"
    content-class="grocery-pm-dialog-content"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div v-if="item" class="spm-wrap">
      <div class="spm-topbar">
        <button
          type="button"
          class="spm-close"
          aria-label="Закрыть"
          @click="close"
        >
          <v-icon size="20">mdi-close</v-icon>
        </button>
      </div>

      <div class="spm-scroll">
      <div class="spm-main">
        <!-- Gallery -->
        <div class="spm-gallery">
          <div v-if="discountPercent > 0" class="spm-discount-badge">
            −{{ discountPercent }}%
          </div>
          <div class="spm-gallery-inner">
            <img
              v-if="activeGallerySrc"
              :src="activeGallerySrc"
              :alt="item.title"
              class="spm-gallery-img"
            />
          </div>
          <button
            v-if="galleryUrls.length > 1"
            type="button"
            class="spm-carousel-arrow"
            aria-label="Следующее фото"
            @click="nextSlide"
          >
            <v-icon size="22">mdi-chevron-right</v-icon>
          </button>
          <div v-if="galleryUrls.length > 1" class="spm-dots" role="tablist">
            <button
              v-for="(url, i) in galleryUrls"
              :key="i"
              type="button"
              class="spm-dot"
              :class="{ 'spm-dot--active': i === carouselIndex }"
              :aria-label="`Фото ${i + 1}`"
              @click="carouselIndex = i"
            />
          </div>
        </div>

        <!-- Info -->
        <div class="spm-info">
          <h2 class="spm-title">{{ item.title }}</h2>
          <p v-if="item.amount" class="spm-subtitle">{{ item.amount }}</p>

          <ul v-if="featureList.length" class="spm-features">
            <li v-for="(line, idx) in featureList" :key="idx">{{ line }}</li>
          </ul>

          <button type="button" class="spm-share" @click="onShare">
            <v-icon size="18">mdi-share-variant-outline</v-icon>
            <span>Поделиться</span>
          </button>

          <p v-if="promoHtml" class="spm-promo" v-html="promoHtml" />

          <p v-if="descriptionText" class="spm-desc">{{ descriptionText }}</p>
          <p v-else class="spm-desc spm-desc--muted">
            Состав, калорийность и условия хранения указаны на упаковке.
          </p>

          <div v-if="nutritionBlock" class="spm-nutrition">
            <div class="spm-nutrition-label">В 100 граммах</div>
            <div class="spm-nutrition-row">
              <div class="spm-nut-cell">
                <div class="spm-nut-val">{{ nutritionBlock.kcal }}</div>
                <div class="spm-nut-unit">Ккал</div>
              </div>
              <div class="spm-nut-cell">
                <div class="spm-nut-val">{{ nutritionBlock.protein }}</div>
                <div class="spm-nut-unit">Белки</div>
              </div>
              <div class="spm-nut-cell">
                <div class="spm-nut-val">{{ nutritionBlock.carbs }}</div>
                <div class="spm-nut-unit">Углеводы</div>
              </div>
            </div>
          </div>

          <div v-if="hasPrice" class="spm-cta-block">
            <button
              v-if="quantity === 0"
              type="button"
              class="spm-cta"
              @click="emitAdd"
            >
              <div class="spm-cta-prices">
                <span v-if="item.old_price" class="spm-cta-old">{{ item.old_price }}</span>
                <span class="spm-cta-cur">{{ item.price }}&nbsp;₽</span>
              </div>
              <span class="spm-cta-plus" aria-hidden="true">+</span>
            </button>
            <div v-else class="spm-cta-inbasket">
              <button type="button" class="spm-step" aria-label="Убрать" @click="emitRemove">
                <v-icon size="22">mdi-minus</v-icon>
              </button>
              <span class="spm-qty">{{ quantity }}</span>
              <button
                type="button"
                class="spm-step"
                :class="{ disabled: maxed }"
                :disabled="maxed"
                aria-label="Добавить"
                @click="emitAdd"
              >
                <v-icon size="22">mdi-plus</v-icon>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="recommendations && recommendations.length" class="spm-rec-block">
        <div class="spm-divider" />
        <h3 class="spm-rec-title">Что ещё пригодится</h3>
        <div class="spm-rec-scroll">
          <button
            v-for="rec in recommendations"
            :key="rec.item_id"
            type="button"
            class="spm-rec-card"
            @click="$emit('select-product', rec)"
          >
            <div class="spm-rec-img-wrap">
              <img v-if="rec.img_url" :src="groceryImageSrc(rec)" :alt="rec.title" />
            </div>
            <div class="spm-rec-meta">
              <div class="spm-rec-name">{{ rec.title }}</div>
              <div v-if="priceOk(rec)" class="spm-rec-price">{{ rec.price }}&nbsp;₽</div>
            </div>
          </button>
        </div>
      </div>
      </div>
    </div>
  </v-dialog>
</template>

<script>
import { defineComponent } from 'vue';
import { groceryImageSrc } from '@/common/groceryImages';

export default defineComponent({
  name: 'GroceryProductModal',
  props: {
    modelValue: { type: Boolean, default: false },
    item: { type: Object, default: null },
    quantity: { type: Number, default: 0 },
    recommendations: { type: Array, default: () => [] },
    maxed: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'add', 'remove', 'select-product'],
  data() {
    return {
      carouselIndex: 0,
    };
  },
  computed: {
    galleryUrls() {
      const it = this.item;
      if (!it) return [];
      const extra = it.detail_img_urls || it.gallery_urls;
      const base = it.img_url ? [groceryImageSrc(it)] : [];
      if (Array.isArray(extra) && extra.length) {
        const merged = [...base];
        extra.forEach((u, i) => {
          const mapped = groceryImageSrc({ img_url: u, item_id: `${it.item_id || 'g'}-${i}` });
          if (mapped && !merged.includes(mapped)) merged.push(mapped);
        });
        return merged;
      }
      return base;
    },
    activeGallerySrc() {
      return this.galleryUrls[this.carouselIndex] || '';
    },
    discountPercent() {
      const it = this.item;
      if (!it || !it.old_price) return 0;
      const cur = parseFloat(it.price);
      const old = parseFloat(it.old_price);
      if (!old || old <= 0 || !cur) return 0;
      const d = Math.round(((old - cur) / old) * 100);
      return d > 0 ? d : 0;
    },
    hasPrice() {
      const p = this.item && this.item.price;
      return !(p === undefined || p === null || String(p).trim() === '');
    },
    featureList() {
      const it = this.item;
      if (!it) return [];
      const raw = it.detail_features ?? it.features;
      if (Array.isArray(raw)) return raw.map(String).filter(Boolean);
      if (typeof raw === 'string') {
        return raw
          .split(/[;\n|]/)
          .map((s) => s.trim())
          .filter(Boolean);
      }
      return [];
    },
    descriptionText() {
      const it = this.item;
      if (!it) return '';
      return it.detail_description || it.description || it.long_description || '';
    },
    promoHtml() {
      const it = this.item;
      if (!it) return '';
      const custom = it.detail_promo_html;
      if (custom) return custom;
      const text = it.detail_promo || it.promo_text;
      const hl = it.promo_highlight || 'подборке';
      if (text) {
        const safe = String(text).replace(/</g, '&lt;').replace(/>/g, '&gt;');
        const escHl = hl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const re = new RegExp(`(${escHl})`, 'i');
        return safe.replace(re, '<span class="spm-promo-hl">$1</span>');
      }
      return `Лучшее из сезона — в нашей <span class="spm-promo-hl">${hl}</span> свежих продуктов.`;
    },
    nutritionBlock() {
      const it = this.item;
      if (!it) return null;
      const n = it.nutrition_100g || it.nutrition;
      if (!n || typeof n !== 'object') return null;
      const kcal = n.kcal ?? n.calories;
      const protein = n.protein ?? n.proteins;
      const carbs = n.carbs ?? n.carbohydrates;
      if (kcal == null && !protein && !carbs) return null;
      return {
        kcal: kcal != null ? String(kcal).replace(',', '.') : '—',
        protein: protein != null ? String(protein) : '—',
        carbs: carbs != null ? String(carbs) : '—',
      };
    },
  },
  watch: {
    modelValue(open) {
      if (open) this.carouselIndex = 0;
    },
    item() {
      this.carouselIndex = 0;
    },
  },
  methods: {
    groceryImageSrc,
    close() {
      this.$emit('update:modelValue', false);
    },
    nextSlide() {
      const n = this.galleryUrls.length;
      if (n <= 1) return;
      this.carouselIndex = (this.carouselIndex + 1) % n;
    },
    emitAdd() {
      if (!this.item || !this.item.item_id || this.maxed) return;
      this.$emit('add', this.item.item_id);
    },
    emitRemove() {
      if (!this.item || !this.item.item_id) return;
      this.$emit('remove', this.item.item_id);
    },
    priceOk(rec) {
      const p = rec && rec.price;
      return !(p === undefined || p === null || String(p).trim() === '');
    },
    onShare() {
      const title = this.item && this.item.title;
      const url = typeof window !== 'undefined' ? window.location.href : '';
      if (navigator.share) {
        navigator.share({ title: title || 'Доставка', url }).catch(() => {});
      }
    },
  },
});
</script>

<style scoped>
.spm-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 32px);
  max-height: min(calc(100dvh - 32px), 920px);
  background: var(--bench-surface-elevated, #fff);
  color: var(--bench-text, #2c3e50);
  border-radius: 32px;
  overflow: hidden;
  font-family:
    system-ui,
    -apple-system,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
}

.spm-topbar {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  padding: 14px 14px 0;
  background: var(--bench-surface-elevated, #fff);
  z-index: 8;
}

.spm-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.spm-close {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: var(--bench-surface, #f0f3f7);
  color: var(--bench-text, #2c3e50);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.spm-close:hover {
  background: var(--bench-primary-light, #e4ebf4);
}

.spm-main {
  display: flex;
  flex-direction: row;
  align-items: stretch;
  min-height: 380px;
}

.spm-gallery {
  flex: 1;
  min-width: 0;
  background: var(--bench-surface, #f0f3f7);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px 40px;
}

.spm-discount-badge {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 2;
  background: var(--bench-header-bg, #3d5a80);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 999px;
}

.spm-gallery-inner {
  width: 100%;
  max-width: 280px;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spm-gallery-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.spm-carousel-arrow {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: var(--bench-surface-elevated, #fff);
  color: var(--bench-text, #2c3e50);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.spm-dots {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}

.spm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  padding: 0;
  background: var(--bench-border, #c5d0de);
  cursor: pointer;
}

.spm-dot--active {
  background: var(--bench-primary, #4a6fa5);
}

.spm-info {
  flex: 1;
  min-width: 0;
  padding: 12px 28px 24px 20px;
  padding-right: 52px;
}

.spm-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--bench-text, #2c3e50);
  margin: 0 0 6px;
  line-height: 1.25;
}

.spm-subtitle {
  margin: 0 0 16px;
  font-size: 15px;
  color: var(--bench-text-muted, #6b7c93);
}

.spm-features {
  margin: 0 0 16px;
  padding-left: 18px;
  color: var(--bench-text, #2c3e50);
  font-size: 14px;
  line-height: 1.5;
}

.spm-features li::marker {
  color: var(--bench-border, #c5d0de);
}

.spm-share {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 999px;
  border: none;
  background: var(--bench-surface, #f0f3f7);
  color: var(--bench-text, #2c3e50);
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 16px;
}

.spm-share:hover {
  background: var(--bench-primary-light, #e4ebf4);
}

.spm-promo {
  font-size: 14px;
  line-height: 1.55;
  color: var(--bench-text, #2c3e50);
  margin: 0 0 14px;
}

:deep(.spm-promo-hl) {
  color: var(--bench-primary, #4a6fa5);
  font-weight: 600;
}

.spm-desc {
  font-size: 14px;
  line-height: 1.55;
  color: var(--bench-text, #2c3e50);
  margin: 0 0 16px;
}

.spm-desc--muted {
  color: var(--bench-text-muted, #6b7c93);
  font-size: 13px;
}

.spm-nutrition {
  border-top: 1px solid var(--bench-border, #c5d0de);
  padding-top: 16px;
  margin-bottom: 16px;
}

.spm-nutrition-label {
  font-size: 13px;
  color: var(--bench-text-muted, #6b7c93);
  margin-bottom: 10px;
}

.spm-nutrition-row {
  display: flex;
  gap: 24px;
}

.spm-nut-cell {
  flex: 1;
}

.spm-nut-val {
  font-size: 22px;
  font-weight: 700;
  color: var(--bench-text, #2c3e50);
}

.spm-nut-unit {
  font-size: 12px;
  color: var(--bench-text-muted, #6b7c93);
  margin-top: 2px;
}

.spm-cta-block {
  margin-top: 8px;
}

.spm-cta {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bench-primary, #4a6fa5);
  color: #fff;
  border: none;
  border-radius: 16px;
  padding: 14px 18px;
  cursor: pointer;
  font-size: 18px;
  font-weight: 700;
}

.spm-cta:hover {
  filter: brightness(1.03);
}

.spm-cta-prices {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.spm-cta-old {
  text-decoration: line-through;
  opacity: 0.85;
  font-size: 16px;
  font-weight: 600;
}

.spm-cta-cur {
  font-size: 20px;
}

.spm-cta-plus {
  font-size: 28px;
  font-weight: 400;
  line-height: 1;
}

.spm-cta-inbasket {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  background: var(--bench-primary, #4a6fa5);
  border-radius: 16px;
  padding: 10px 16px;
}

.spm-step {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spm-step.disabled {
  opacity: 0.45;
  cursor: default;
}

.spm-qty {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  min-width: 28px;
  text-align: center;
}

.spm-divider {
  height: 1px;
  background: var(--bench-border, #c5d0de);
  margin: 0 24px;
}

.spm-rec-block {
  padding-bottom: 20px;
}

.spm-rec-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--bench-text, #2c3e50);
  margin: 18px 24px 12px;
}

.spm-rec-scroll {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 0 24px 8px;
  scrollbar-width: thin;
}

.spm-rec-card {
  flex: 0 0 120px;
  width: 120px;
  border: 1px solid var(--bench-border, #c5d0de);
  border-radius: 16px;
  background: var(--bench-surface-elevated, #fff);
  padding: 0;
  cursor: pointer;
  text-align: left;
  overflow: hidden;
}

.spm-rec-card:hover {
  border-color: var(--bench-primary-muted, #6b8cae);
}

.spm-rec-img-wrap {
  height: 100px;
  background: var(--bench-surface, #f0f3f7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.spm-rec-img-wrap img {
  max-width: 90%;
  max-height: 90px;
  object-fit: contain;
}

.spm-rec-meta {
  padding: 8px 10px 10px;
}

.spm-rec-name {
  font-size: 12px;
  line-height: 1.3;
  color: var(--bench-text, #2c3e50);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 2.6em;
}

.spm-rec-price {
  font-size: 14px;
  font-weight: 700;
  color: var(--bench-text, #2c3e50);
  margin-top: 4px;
}

@media (max-width: 720px) {
  .spm-wrap {
    max-height: calc(100vh - 24px);
    max-height: min(calc(100dvh - 24px), 920px);
  }

  .spm-main {
    flex-direction: column;
    min-height: unset;
  }

  .spm-gallery {
    padding: 40px 16px 36px;
  }

  .spm-info {
    padding: 12px 20px 16px;
    padding-right: 20px;
  }

  .spm-nutrition-row {
    gap: 12px;
  }
}
</style>

<style>
/* Teleported Vuetify dialog — tokens must live outside scoped + .bench-grocery */
.grocery-pm-dialog-content .v-overlay__content {
  padding: 12px;
  background: transparent !important;
}

.grocery-pm-dialog .v-overlay__content,
.v-overlay.grocery-pm-dialog .v-overlay__content {
  background: transparent !important;
  box-shadow: none !important;
}

html[data-bench-theme="dark"] .spm-wrap,
html[data-bench-theme="dark"] .spm-topbar,
html[data-bench-theme="dark"] .spm-rec-card {
  background: var(--bench-surface-elevated) !important;
  color: var(--bench-text) !important;
}
</style>
