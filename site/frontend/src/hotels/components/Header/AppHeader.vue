<template>
  <header>
    <HeaderLogo />
    <HeaderWidgets />
  </header>
</template>

<script setup lang="ts">
import HeaderLogo from "./components/HeaderLogo.vue";
import HeaderWidgets from "./components/HeaderWidgets.vue";
</script>

<style scoped>
header {
  align-items: center;
  block-size: 48px;
  display: flex;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  justify-content: left;

  background: var(--bench-surface-elevated, #fff);
}
</style>
