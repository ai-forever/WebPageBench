<template>
  <component :is="variantComponent" v-bind="$attrs" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useBenchUiVariant } from './useBenchUiVariant';
import DateSplitPopup from './date/DateSplitPopup.vue';
import DateInlineCalendar from './date/DateInlineCalendar.vue';
import DateTextInput from './date/DateTextInput.vue';
import DateSinglePopup from './date/DateSinglePopup.vue';

defineOptions({ inheritAttrs: false });

const { variant } = useBenchUiVariant('date', 'hotels');

const MAP: Record<string, object> = {
  split_popup: DateSplitPopup,
  inline_calendar: DateInlineCalendar,
  text_input: DateTextInput,
  single_popup: DateSinglePopup,
};

const variantComponent = computed(() => MAP[variant.value] || DateSplitPopup);
</script>
