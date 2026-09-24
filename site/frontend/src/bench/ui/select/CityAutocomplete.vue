<template>
  <DestinationPicker v-bind="$attrs" />
</template>

<script setup lang="ts">
import DestinationPicker from '@/hotels/components/Home/DestinationPicker.vue';

defineOptions({ inheritAttrs: false });
</script>
