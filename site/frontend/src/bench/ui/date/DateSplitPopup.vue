<template>
  <DateRangeField v-bind="$attrs" />
</template>

<script setup lang="ts">
import DateRangeField from '@/hotels/components/DateRangePicker/DateRangeField.vue';

defineOptions({ inheritAttrs: false });
</script>
