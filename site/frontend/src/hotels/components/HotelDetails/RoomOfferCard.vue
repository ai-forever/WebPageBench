<template>
  <article class="offer">
    <div class="imgWrap">
      <img class="img" :src="offer.imageUrl" alt="" />
    </div>

    <div class="mid">
      <div class="roomTitle">{{ offer.roomName }}</div>
      <div class="roomBeds">{{ offer.bedLabel }}</div>

      <ul class="props">
        <li class="prop">
          <span class="ico meal"></span>
          <span class="txt">{{ mealText }}</span>
        </li>
        <li class="prop">
          <span class="ico cancellation"></span>
          <span class="txt">{{ cancellationText }}</span>
        </li>
        <li class="prop">
          <span class="ico payment"></span>
          <span class="txt">{{ paymentText }}</span>
        </li>
      </ul>
    </div>

    <div class="right">
      <div class="price">{{ rub.format(offer.totalRub) }}</div>
      <div class="hint">за {{ nights }} {{ nightsWord }} • {{ roomsGuestsText }}</div>
      <button class="btn" type="button">Выбрать</button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type RoomOffer = {
  id: string;
  roomName: string;
  bedLabel: string;
  meal: 'none' | 'breakfast';
  cancellation: 'free' | 'no_free';
  payment: 'online' | 'at_hotel';
  totalRub: number;
  imageUrl: string;
};

const props = defineProps<{
  offer: RoomOffer;
  nights: number;
  guests: number;
  rooms: number;
  children: number;
}>();

const rub = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 });

function pluralRu(n: number, one: string, few: string, many: string) {
  const n10 = n % 10;
  const n100 = n % 100;
  if (n10 === 1 && n100 !== 11) return one;
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few;
  return many;
}

const nightsWord = computed(() => pluralRu(props.nights, 'ночь', 'ночи', 'ночей'));

const roomsGuestsText = computed(() => {
  const r = props.rooms;
  const g = props.guests;
  const c = props.children;
  const roomsPart = `${r} ${pluralRu(r, 'номер', 'номера', 'номеров')}`;
  const guestsPart = `${g} ${pluralRu(g, 'гость', 'гостя', 'гостей')}`;
  const childrenPart = c > 0 ? `, ${c} ${pluralRu(c, 'ребёнок', 'ребёнка', 'детей')}` : '';
  return `${roomsPart} • ${guestsPart}${childrenPart}`;
});

const mealText = computed(() => (props.offer.meal === 'breakfast' ? 'Завтрак включён' : 'Питание не включено'));
const cancellationText = computed(() => (props.offer.cancellation === 'free' ? 'Бесплатная отмена' : 'Без беспл. отмены'));
const paymentText = computed(() => (props.offer.payment === 'at_hotel' ? 'Оплата в отеле' : 'Оплата на сайте'));
</script>

<style scoped>
.offer {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) 220px;
  gap: 12px;
  border-radius: 16px;
  border: 1px solid rgba(45, 49, 55, 0.10);
  overflow: hidden;
  background: var(--bench-surface-elevated, #fff);
}

.imgWrap {
  padding: 8px;
  display: flex;
  align-items: stretch;
}

.img {
  width: 100%;
  height: 118px;
  object-fit: cover;
  border-radius: 12px;
  display: block;
}

.mid {
  padding: 10px 0;
  min-width: 0;
}

.roomTitle {
  font-size: 14px;
  line-height: 18px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.roomBeds {
  margin-top: 4px;
  font-size: 12px;
  line-height: 16px;
  font-weight: 500;
  color: #868686;
  text-transform: lowercase;
}

.props {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 6px;
}

.prop {
  display: flex;
  align-items: center;
  gap: 8px;
}

.txt {
  font-size: 12px;
  line-height: 16px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
}

.ico {
  width: 16px;
  height: 16px;
  background-color: var(--bench-text, #2d3137);
  mask-position: center;
  mask-repeat: no-repeat;
  mask-size: contain;
  flex-shrink: 0;
}

/* иконки как у тебя в карточке */
.meal {
  mask-image: url(/hotels/cdn/meal.418dda29.svg);
}
.cancellation {
  mask-image: url(/hotels/cdn/cancellation.398c95fa.svg);
}
.payment {
  mask-image: url(/hotels/cdn/payment.2db08cdd.svg);
}

.right {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 8px;
}

.price {
  font-size: 18px;
  line-height: 22px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  text-align: right;
}

.hint {
  font-size: 12px;
  line-height: 16px;
  font-weight: 500;
  color: rgba(45, 49, 55, 0.65);
  text-align: right;
}

.btn {
  width: 100%;
  height: 40px;
  border-radius: 12px;
  border: 0;
  background: #0e41d2;
  color: #fff;
  cursor: pointer;
  font-family: PTRootUI, Verdana, sans-serif;
  font-weight: 600;
  font-size: 14px;
}

@media (max-width: 920px) {
  .offer {
    grid-template-columns: 1fr;
  }
  .right {
    align-items: stretch;
  }
  .btn {
    width: 100%;
  }
}
</style>
