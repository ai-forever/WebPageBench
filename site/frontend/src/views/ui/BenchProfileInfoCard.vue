<template>
  <div class="bench-profile-info-card" :class="variantClass">
    <div v-if="showGreeting" class="bench-profile-info-card__hello">Здравствуйте</div>
    <div class="bench-profile-info-card__name">{{ info.fullName }}</div>
    <div v-if="info.email" class="bench-profile-info-card__detail">{{ info.email }}</div>
    <div v-if="info.phone" class="bench-profile-info-card__detail bench-profile-info-card__detail--compact">{{ info.phone }}</div>
    <div v-if="info.address" class="bench-profile-info-card__detail bench-profile-info-card__detail--compact">{{ info.address }}</div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'BenchProfileInfoCard',
  props: {
    info: {
      type: Object,
      required: true,
    },
    variant: {
      type: String,
      default: 'card',
    },
    showGreeting: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    variantClass() {
      return `bench-profile-info-card--${this.variant}`;
    },
  },
});
</script>

<style src="@/assets/bench-profile.css"></style>
