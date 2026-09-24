<template>
  <div class="zenforminput zenforminput-size-l">
    <div class="zenforminput-inner">
      <label class="zenforminput-title-wrapper" :for="id">
        <p class="zenforminput-title">{{ label }}</p>
        <div class="zenforminput-tip"></div>
      </label>

      <div class="zenforminput-control">
        <input
          class="zenforminputcontrol"
          :id="id"
          :name="name"
          :placeholder="placeholder"
          :type="type"
          :value="modelValue"
          :aria-label="placeholder"
          dir="ltr"
          @input="onInput"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
type Props = {
  modelValue: string;
  id: string;
  name: string;
  label: string;
  placeholder?: string;
  type?: string;
};

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "update:modelValue", v: string): void;
}>();

function onInput(e: Event) {
  emit("update:modelValue", (e.target as HTMLInputElement).value);
}
</script>

<style scoped>
.zenforminput-inner {
  display: block;
  position: relative;
  transition: box-shadow 0.16s ease;

  background-color: white;
  border-radius: 12px;
  box-shadow: 0 0 0 1px rgba(45, 49, 55, 0.15);
  max-height: 56px;
}

.zenforminput-control {
  line-height: 20px !important;
}

.zenforminput-size-l .zenforminput-inner {
  padding: 4px 16px 10px;
}

.zenforminput-title-wrapper {
  display: inline-flex;
  max-width: 100%;
}

.zenforminput-title {
  color: var(--bench-text, #2d3137);
  line-height: 17px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zenforminput-size-l .zenforminput-title {
  font-size: 12px;
  margin-bottom: 5px;
}

.zenforminput-tip {
  margin-left: 8px;
  margin-top: -2px;
  z-index: 2;
}

.zenforminputcontrol {
  width: 100%;
  background-color: transparent;

  color: var(--bench-text, #2d3137);
  font-size: 16px !important;
  line-height: 1.25;
  outline: 0;
  border: 0;
  padding: 0;
}
</style>
