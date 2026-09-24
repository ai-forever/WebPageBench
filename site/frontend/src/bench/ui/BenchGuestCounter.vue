<template>
  <component :is="variantComponent" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useBenchUiVariant } from './useBenchUiVariant';
import GuestRoomsPopup from './counter/GuestRoomsPopup.vue';
import GuestInlineStepper from './counter/GuestInlineStepper.vue';
import GuestCompactSelect from './counter/GuestCompactSelect.vue';
import GuestPillButtons from './counter/GuestPillButtons.vue';

const { variant } = useBenchUiVariant('counter_guests', 'hotels');

const MAP: Record<string, object> = {
  rooms_popup: GuestRoomsPopup,
  inline_stepper: GuestInlineStepper,
  compact_select: GuestCompactSelect,
  pill_buttons: GuestPillButtons,
};

const variantComponent = computed(() => MAP[variant.value] || GuestRoomsPopup);
</script>
