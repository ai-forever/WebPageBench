<template>
  <component :is="variantComponent" v-bind="$attrs" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useBenchUiVariant } from './useBenchUiVariant';
import CityAutocomplete from './select/CityAutocomplete.vue';
import CityNativeSelect from './select/CityNativeSelect.vue';

defineOptions({ inheritAttrs: false });

const { variant } = useBenchUiVariant('select_city', 'hotels');

const MAP: Record<string, object> = {
  autocomplete: CityAutocomplete,
  native_select: CityNativeSelect,
};

const variantComponent = computed(() => MAP[variant.value] || CityAutocomplete);
</script>
