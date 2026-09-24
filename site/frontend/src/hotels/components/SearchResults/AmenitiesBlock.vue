<template>
  <section v-if="amenities" class="Amenities">
    <h2 class="AmenitiesTitle">{{ amenities.title ?? 'Услуги и удобства' }}</h2>

    <div class="AmenitiesList">
      <div
        v-for="g in amenities.groups"
        :key="g.id"
        class="Group"
        :class="{ 'Group--popular': g.variant === 'popular' }"
      >
        <div class="GroupHeader" :class="iconClass(g.icon)">
          <h3 class="GroupTitle">{{ g.title }}</h3>
        </div>

        <ul class="GroupAmenities">
          <li v-for="(it, idx) in g.items" :key="g.id + '-' + idx" class="Amenity">
            <div class="AmenityText">{{ itemText(it) }}</div>
            <p v-if="itemNote(it)" class="Chargeable">{{ itemNote(it) }}</p>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';

type AmenityItem = string | { text: string; note?: string };

type AmenitiesGroup = {
  id: string;
  title: string;
  icon?: string; // ключ иконки (см. CSS)
  variant?: 'popular';
  items: AmenityItem[];
};

type AmenitiesBlock = {
  title?: string;
  groups: AmenitiesGroup[];
};

type HotelWithAmenities = {
  id: string;
  amenitiesBlock?: AmenitiesBlock;
};

const props = defineProps<{ hotel: HotelWithAmenities }>();

const amenities = computed(() => props.hotel.amenitiesBlock ?? null);

function itemText(it: AmenityItem) {
  return typeof it === 'string' ? it : it.text;
}
function itemNote(it: AmenityItem) {
  return typeof it === 'string' ? '' : (it.note ?? '');
}

function iconClass(icon?: string) {
  return icon ? `GroupHeader--${icon}` : '';
}
</script>

<style scoped>
.Amenities {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  overflow: hidden;
  padding: 24px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.AmenitiesTitle {
  margin: 0 0 16px;
  color: var(--bench-text, #2d3137);
  font-size: 24px;
  font-weight: 800;
  line-height: 30px;
  font-family: PTRootUI, Verdana, sans-serif;
}

/* как на скрине — “колоночная” раскладка (masonry-подобно) */
.AmenitiesList {
  column-count: 4;
  column-gap: 40px;
}

.Group {
  display: inline-block;
  width: 100%;
  break-inside: avoid;
  margin: 0 0 24px;
}

.Group--popular {
  background: var(--bench-primary-light, #f8f8f8);
  border-radius: 16px;
  padding: 12px;
}

.GroupHeader {
  display: flex;
  align-items: baseline;
  color: var(--bench-text, #2d3137);
  margin: 0 0 10px;
}

.GroupHeader::before {
  align-self: baseline;
  background-color: var(--bench-text, #2d3137);
  block-size: 20px;
  inline-size: 20px;
  content: "";
  display: block;
  flex-shrink: 0;
  margin-inline-end: 8px;

  -webkit-mask-image: url(/hotels/cdn/default-dark.0cf44b86.svg);
  mask-image: url(/hotels/cdn/default-dark.0cf44b86.svg);
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-size: contain;
  mask-size: contain;
}

/* POPULAR — не mask, а background-image */
.GroupHeader--popular::before {
  background-color: unset;
  -webkit-mask-image: none;
  mask-image: none;
  background-image: url(/hotels/cdn/popular.46afefb4.svg);
  background-position: 50%;
  background-repeat: no-repeat;
  background-size: contain;
}

/* остальные — через mask-image */
.GroupHeader--common_info::before {
  -webkit-mask-image: url(/hotels/cdn/common-info.5208dc13.svg);
  mask-image: url(/hotels/cdn/common-info.5208dc13.svg);
}
.GroupHeader--extra_service::before {
  -webkit-mask-image: url(/hotels/cdn/extra-service.1faf2bfd.svg);
  mask-image: url(/hotels/cdn/extra-service.1faf2bfd.svg);
}
.GroupHeader--disabled_support::before {
  -webkit-mask-image: url(/hotels/cdn/disabled-support.cc65e41d.svg);
  mask-image: url(/hotels/cdn/disabled-support.cc65e41d.svg);
}
.GroupHeader--extra_services::before {
  -webkit-mask-image: url(/hotels/cdn/extra-services.7bf34de9.svg);
  mask-image: url(/hotels/cdn/extra-services.7bf34de9.svg);
}
.GroupHeader--meal::before {
  -webkit-mask-image: url(/hotels/cdn/meal.27c89335.svg);
  mask-image: url(/hotels/cdn/meal.27c89335.svg);
}
.GroupHeader--internet::before {
  -webkit-mask-image: url(/hotels/cdn/internet.b8e3abca.svg);
  mask-image: url(/hotels/cdn/internet.b8e3abca.svg);
}
.GroupHeader--shuttle::before {
  -webkit-mask-image: url(/hotels/cdn/shuttle.3f845299.svg);
  mask-image: url(/hotels/cdn/shuttle.3f845299.svg);
}
.GroupHeader--languages::before {
  -webkit-mask-image: url(/hotels/cdn/languages.14395ccf.svg);
  mask-image: url(/hotels/cdn/languages.14395ccf.svg);
}
.GroupHeader--tours::before {
  -webkit-mask-image: url(/hotels/cdn/tours.c4e2a46c.svg);
  mask-image: url(/hotels/cdn/tours.c4e2a46c.svg);
}
.GroupHeader--pool::before {
  -webkit-mask-image: url(/hotels/cdn/pool.3a7ca567.svg);
  mask-image: url(/hotels/cdn/pool.3a7ca567.svg);
}
.GroupHeader--barber_shop::before {
  -webkit-mask-image: url(/hotels/cdn/barber-shop.ed6a092e.svg);
  mask-image: url(/hotels/cdn/barber-shop.ed6a092e.svg);
}
.GroupHeader--pets::before {
  -webkit-mask-image: url(/hotels/cdn/pets.383546b8.svg);
  mask-image: url(/hotels/cdn/pets.383546b8.svg);
}
.GroupHeader--anticovid::before {
  -webkit-mask-image: url(/hotels/cdn/anticovid.d3b20810.svg);
  mask-image: url(/hotels/cdn/anticovid.d3b20810.svg);
}

.GroupTitle {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.GroupAmenities {
  margin: 0;
  padding-inline-start: 18px;
}

::marker {
  color: #c8c8c8 !important;
}

.Amenity {
  margin-block-end: 8px;
}

.AmenityText {
  color: var(--bench-text, #2d3137);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.Chargeable {
  margin: 2px 0 0;
  color: #868686;
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  font-family: PTRootUI, Verdana, sans-serif;
}

/* адаптив */
@media (max-width: 1200px) {
  .AmenitiesList { column-count: 3; }
}
@media (max-width: 980px) {
  .AmenitiesList { column-count: 2; }
}
@media (max-width: 600px) {
  .AmenitiesList { column-count: 1; }
  .AmenitiesTitle { font-size: 24px; line-height: 30px; }
}
</style>
