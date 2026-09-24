<template>
  <div class="wrap">
    <FieldShell as="button" clickable class="cell left">
      <template #label>Заезд</template>
      <div class="value">{{ checkIn }}</div>
    </FieldShell>

    <FieldShell as="button" clickable class="cell right">
      <template #label>Выезд</template>
      <div class="value">{{ checkOut }}</div>
    </FieldShell>
  </div>
</template>

<script setup>
import FieldShell from './FieldShell.vue';

defineProps({
  checkIn: { type: String, required: true },
  checkOut: { type: String, required: true },
});
</script>

<style scoped>
.wrap {
  display: inline-flex;
  inline-size: 100%;
  align-items: flex-start;
}

.cell {
  flex: 1 1 0;
  min-inline-size: 100px;
  position: relative;

  border-radius: 0 !important;
}

/* “склейка” рамок */
.cell + .cell {
  margin-inline-start: -1px;
}

/* крайние радиусы */
.left {
  border-start-start-radius: 12px !important;
  border-end-start-radius: 12px !important;
}

.right {
  border-start-end-radius: 12px !important;
  border-end-end-radius: 12px !important;
}

/* z-index чтобы активный бордер был сверху */
.cell:hover,
.cell:focus-within {
  z-index: 2;
}

.value {
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  white-space: nowrap;
  font-family: PTRootUI;
}
</style>
