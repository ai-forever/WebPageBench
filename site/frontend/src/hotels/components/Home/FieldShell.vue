<template>
  <component
    :is="as"
    class="field"
    :class="{ clickable, autoHeight }"
    v-bind="$attrs"
    :type="as === 'button' ? 'button' : undefined"
  >
    <div class="label">
      <slot name="label" />
    </div>

    <div class="body">
      <slot />
      <slot name="right" />
    </div>
  </component>
</template>

<script setup>
defineProps({
  as: { type: String, default: 'div' },       // 'div' | 'button'
  clickable: { type: Boolean, default: false },
  autoHeight: { type: Boolean, default: false },
});
</script>

<style scoped>
.field {
  box-sizing: border-box;
  inline-size: 100%;
  block-size: 48px;

  display: flex;
  flex-direction: column;
  justify-content: center;

  padding: 3px 11px 5px;
  border-radius: 12px;
  border: 1px solid rgba(41, 47, 55, 0.12);
  background: var(--bench-surface-elevated, #fff);

  transition: border-color 0.16s ease, box-shadow 0.16s ease;
}

.field:hover {
  border-color: #0e41d2;
}

.field.clickable {
  appearance: none;
  text-align: left;
  cursor: pointer;
  border: 1px solid rgba(41, 47, 55, 0.12);
}

.field.clickable:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 3px rgba(14, 65, 210, 0.15);
  border-color: #0e41d2;
}

.label {
  font-size: 12px;
  line-height: 16px;
  font-weight: 400;
  color: rgba(45, 49, 55, 0.85);
  margin-block-end: 2px;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: PTRootUI;
}

.field.autoHeight {
  block-size: auto;
  min-block-size: 48px;
  padding-block: 8px;
}

.body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-block-size: 20px;
  flex-wrap: wrap;
}
</style>
