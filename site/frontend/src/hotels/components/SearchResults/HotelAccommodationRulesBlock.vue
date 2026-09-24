<template>
  <section v-if="acc" class="Accommodation">
    <div class="shell">
      <h3 class="title">{{ acc.title ?? 'Условия размещения' }}</h3>

      <div class="grid">
        <!-- CHECK IN/OUT (серый блок) -->
        <div v-if="acc.checkInOut" class="policy policy--bg policy--check">
          <div class="policyTitle policyTitle--hasIcon policyTitle--checkin policyTitle--checkinout">
            {{ acc.checkInOut.title }}
          </div>

          <div class="checkRow">
            <div class="checkCol">
              <div class="checkHead">{{ acc.checkInOut.checkIn.label }}</div>
              <div class="checkVal">{{ acc.checkInOut.checkIn.value }}</div>
            </div>

            <div class="checkCol">
              <div class="checkHead">{{ acc.checkInOut.checkOut.label }}</div>
              <div class="checkVal">{{ acc.checkInOut.checkOut.value }}</div>
            </div>
          </div>
        </div>

        <!-- OTHER POLICIES -->
        <div v-for="b in acc.blocks" :key="b.id" class="policy">
          <div
            class="policyTitle policyTitle--hasIcon"
            :class="`policyTitle--${b.icon}`"
          >
            {{ b.title }}
          </div>

          <ul class="list">
            <li v-for="(it, i) in b.items" :key="b.id + '-' + i" class="item">
              <div class="itemText">{{ it.label }}</div>
              <div v-if="it.value" class="itemValue">{{ it.value }}</div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type CheckPart = { label: string; value: string };

type AccommodationItem = {
  label: string;
  value?: string;
};

type AccommodationBlockItem = {
  id: string;
  title: string;
  icon: 'deposit' | 'extraBed' | 'pets' | string;
  items: AccommodationItem[];
};

type AccommodationBlock = {
  title?: string;
  checkInOut?: {
    title: string;
    checkIn: CheckPart;
    checkOut: CheckPart;
  };
  blocks: AccommodationBlockItem[];
};

type HotelWithAccommodation = {
  id: string;
  accommodationBlock?: AccommodationBlock;
};

const props = defineProps<{ hotel: HotelWithAccommodation }>();

const acc = computed(() => props.hotel.accommodationBlock ?? null);
</script>

<style scoped>
.shell {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  overflow: hidden;
  padding: 24px;
  font-family: PTRootUI, Verdana, sans-serif;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
}

.title {
  margin: 0 0 16px;
  color: var(--bench-text, #2d3137);
  font-size: 24px;
  font-weight: 700;
  line-height: 30px;
}

/* layout like screenshot */
.grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr 1fr 1fr;
  gap: 24px;
  align-items: start;
}

.policy {
  min-width: 0;
  display: flex;
  gap: 8px;
  flex-direction: column;
}

.policy--bg {
  background: var(--bench-primary-light, #f8f8f8);
  border-radius: 12px;
  padding: 12px;
}

.policyTitle {
  position: relative;
  padding-inline-start: 24px;
  color: var(--bench-text, #2d3137);
  font-size: 16px;
  font-weight: 800;
  line-height: 20px;
  /* margin-bottom: 12px; */
}

/* icons via ::before (mask) exactly as original approach */
.policyTitle--hasIcon::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 0;
  inline-size: 16px;
  block-size: 16px;
  transform: translateY(-50%);
  background-color: currentColor;
  background-repeat: no-repeat;
  background-size: contain;
  -webkit-mask-size: contain;
  mask-size: contain;
}

/* checkin/out icon is slightly bigger */
.policyTitle--checkinout::before {
  inline-size: 19px;
  block-size: 19px;
}

.policyTitle--checkin::before {
  -webkit-mask: url(/hotels/cdn/checkin.8d4e37c0.svg) no-repeat center;
  mask: url(/hotels/cdn/checkin.8d4e37c0.svg) no-repeat center;
}

.policyTitle--deposit::before {
  -webkit-mask: url(/hotels/cdn/deposit.f18fa46d.svg) no-repeat center;
  mask: url(/hotels/cdn/deposit.f18fa46d.svg) no-repeat center;
}

.policyTitle--extraBed::before {
  -webkit-mask: url(/hotels/cdn/extraBed.24fe62c6.svg) no-repeat center;
  mask: url(/hotels/cdn/extraBed.24fe62c6.svg) no-repeat center;
}

.policyTitle--pets::before {
  -webkit-mask: url(/hotels/cdn/pets.c1d997ec.svg) no-repeat center;
  mask: url(/hotels/cdn/pets.c1d997ec.svg) no-repeat center;
}

/* checkin/out inner */
.checkRow {
  display: flex;
  gap: 8px;
  margin-inline-start: 28px;
  flex-direction: column;
}

.checkCol {
  min-width: 0;
}

.checkHead {
  color: #868686;
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
  margin-bottom: 6px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.checkVal {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

/* list items like original */
.list {
  margin: 0;
  padding: 0;
  /* list-style: disc; */
  display: flex;
  gap: 8px;
  flex-direction: column;
  list-style: none;
  position: relative;
  margin-inline-start: 10px;
}

.list::before {
  color: #c8c8c8 !important;
  content: "•";
  position: absolute;
  left: -10px;
}

.item + .item {
  margin-top: 10px;
}

.itemText {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.itemValue {
  margin-top: 4px;
  color: #868686;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

/* responsive */
@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr 1fr;
  }
  .policy--check {
    grid-column: 1 / -1;
  }
}

@media (max-width: 720px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
