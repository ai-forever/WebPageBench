<template>
  <label class="zencheckbox">
    <input class="zencheckbox-input visuallyhidden" type="checkbox" :checked="modelValue" @change="onChange" />
    <div class="zencheckbox-inner">
      <slot />
    </div>
    <div class="zencheckbox-styled-checkbox"></div>
  </label>
</template>

<script setup lang="ts">
const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{ (e: "update:modelValue", v: boolean): void }>();

function onChange(e: Event) {
  emit("update:modelValue", (e.target as HTMLInputElement).checked);
}
</script>

<style scoped>
.zencheckbox {
  -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
  display: inline-flex;
  flex-direction: row-reverse;
  position: relative;
  cursor: pointer;

  align-items: center;

  max-width: 100%;
  white-space: normal;
}

.visuallyhidden {
  position: absolute;
  inline-size: 1px;
  block-size: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  border: 0;
  margin: -1px;
  padding: 0;
}

.zencheckbox-inner {
  display: inline;
}

.zencheckbox-text {
  display: inline;
  font-size: 14px !important;
  line-height: 18px !important;
  white-space: normal;
}

.zencheckbox-styled-checkbox {
  box-sizing: border-box;
  display: inline-block;
  flex: 1 0 auto;
  height: 16px;
  width: 16px;
  position: relative;
  transition: all 0.16s;
  will-change: background;

  margin-right: 8px;
  margin-top: 1px;

  background-clip: content-box;
  background-color: var(--box-bg, #fff);
  border: 1px solid var(--box-border, rgba(45, 49, 55, 0.25));
  border-radius: 4px;
  transform: translateZ(0);
}

.zencheckbox-input ~ .zencheckbox-styled-checkbox::after {
  box-sizing: content-box;
  content: "";
  display: block;
  height: 8px;
  width: 4px;
  opacity: 0;
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(45deg);

  border-bottom: 2px solid var(--box-on-typo, #fff);
  border-right: 2px solid var(--box-on-typo, #fff);
}

.zencheckbox-input:checked ~ .zencheckbox-styled-checkbox {
  background-color: var(--link, #0e41d2);
  border-color: var(--link, #0e41d2);
}

.zencheckbox-input:checked ~ .zencheckbox-styled-checkbox::after {
  opacity: 1;
}
</style>
