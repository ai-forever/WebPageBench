<template>
  <div class="PaymentSection">
    <!-- LEFT: Payment (из JSON) -->
    <section v-if="payment" class="SectionCard">
      <h3 class="SectionTitle">{{ payment.title ?? 'Оплата' }}</h3>

      <div class="SectionContent">
        <!-- In hotel -->
        <div class="PolicyBlock">
          <div class="PolicyTitle">{{ payment.inHotelTitle ?? 'В отеле' }}</div>

          <ul class="PolicyList">
            <li v-for="(it, idx) in (payment.inHotelItems ?? [])" :key="idx" class="PolicyListItem">
              <template v-if="it.type === 'text'">
                <div class="PolicyText">{{ formatText(it.text) }}</div>
              </template>

              <template v-else-if="it.type === 'cards'">
                <div class="PolicyText">{{ it.label }}</div>

                <div class="CardsRow">
                  <img
                    v-for="logo in logosByBrands(it.codes ?? it.brands ?? [])"
                    :key="logo.src"
                    class="CardLogo"
                    :src="logo.src"
                    :alt="logo.alt"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
              </template>
            </li>
          </ul>
        </div>

        <!-- On site -->
        <div class="PolicyBlock">
          <div class="PolicyTitle">{{ payment.onSiteTitle ?? 'На сайте' }}</div>
          <p class="PolicyParagraph">{{ payment.onSiteText }}</p>
        </div>
      </div>
    </section>

    <!-- RIGHT: Corp (статично, всегда) -->
    <section class="SectionCard">
      <h3 class="SectionTitle">Корпоративным клиентам</h3>

      <div class="CorpContent">
        <p class="CorpText">
          Если вы хотите оплатить заказ безналичным способом как юридическое лицо, пожалуйста, напишите на
          <a class="CorpLink" :href="`mailto:${CORP_EMAIL}`">{{ CORP_EMAIL }}</a>
        </p>

        <a class="CorpBtn" :href="CORP_READ_MORE_URL" target="_blank" rel="noopener noreferrer">
          Узнать больше
        </a>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type PaymentItem =
  | { type: 'text'; text: string }
  | { type: 'cards'; label: string; codes?: string[]; brands?: string[] };

type PaymentBlock = {
  title?: string;
  inHotelTitle?: string;
  onSiteTitle?: string;
  inHotelItems: PaymentItem[];
  onSiteText: string;
};

type HotelWithPayment = {
  id: string;
  currencyCode?: string; // например "CHF"
  paymentSection?: {
    payment?: PaymentBlock;
  };
};

const props = defineProps<{ hotel: HotelWithPayment }>();

// ✅ было paymentBlock, теперь paymentSection.payment
const payment = computed(() => props.hotel.paymentSection?.payment ?? null);

/** статичные данные корп-блока */
const CORP_EMAIL = 'corp@example.com';
const CORP_READ_MORE_URL = '/hotels/cdn/corp_product.bin';

/** статичная мапа лого по коду */
const PAYMENT_LOGOS: Record<string, { src: string; alt: string }> = {
  visa: {
    src: '/hotels/cdn/visa.0c8ebf07.svg',
    alt: 'Visa',
  },
  mastercard: {
    src: '/hotels/cdn/mastercard.20c7c6b7.svg',
    alt: 'Mastercard',
  },
  'american-express': {
    src: '/hotels/cdn/american-express.37fc48ef.svg',
    alt: 'American Express',
  },
  dinersclub: {
    src: '/hotels/cdn/dinersclub.ece35638.svg',
    alt: 'Diners Club',
  },
};

function logosByBrands(brands: string[]) {
  return (brands ?? [])
    .map((code) => PAYMENT_LOGOS[String(code).toLowerCase()])
    .filter(Boolean);
}

function formatText(text: string) {
  const cur = props.hotel.currencyCode ?? 'CHF';
  // @ts-ignore
  return String(text ?? '').replaceAll('{CURRENCY}', cur);
}
</script>

<style scoped>
/* твои стили без изменений */
.PaymentSection {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.SectionCard {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  overflow: hidden;
  padding: 24px;
  font-family: PTRootUI, Verdana, sans-serif;

  flex: 1 1 calc(50% - 10px);
  min-width: 340px;
}

.SectionTitle {
  color: var(--bench-text, #2d3137);
  font-size: 24px;
  font-weight: 700;
  line-height: 30px;
  margin: 0 0 16px;
  position: relative;
  font-family: PTRootUI, Verdana, sans-serif;
}

.SectionContent {
  display: grid;
  gap: 18px;
}

.PolicyBlock {
  display: grid;
  gap: 10px;
}

.PolicyTitle {
  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 700;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.PolicyList {
  margin: 0;
  padding-inline-start: 18px;
}

::marker {
  color: #c8c8c8 !important;
}

.PolicyListItem {
  margin-block-end: 10px;
}

.PolicyText {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.PolicyParagraph {
  margin: 0;
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
}

.CardsRow {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.CardLogo {
  block-size: 22px;
  display: inline-block;
  max-inline-size: 117px;
}

/* corp */
.CorpContent {
  display: grid;
  gap: 18px;
}

.CorpText {
  margin: 0;
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
}

.CorpLink {
  color: #0e41d2;
  text-decoration: none;
  font-weight: 600;
}
.CorpLink:hover {
  text-decoration: underline;
}

.CorpBtn {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  background: var(--bench-primary-light, rgb(236, 241, 251)) !important;
  color: var(--bench-primary, #0e41d2);
  text-decoration: none;
  font-weight: 500;
  font-size: 16px;
  line-height: 20px;
}

@media (max-width: 980px) {
  .SectionCard {
    flex: 1 1 100%;
    min-width: 0;
  }
}
</style>
