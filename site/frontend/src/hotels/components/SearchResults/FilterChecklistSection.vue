<template>
  <section class="section">
    <div v-if="title" class="sectionTitle">{{ title }}</div>
    <div v-if="subtitle" class="sectionSubtitle">{{ subtitle }}</div>

    <div class="list">
      <div
        v-for="it in items"
        :key="it.key"
        class="row"
        :class="{ rowDisabled: isDisabled(it) }"
      >
        <label class="rowLeft">
          <!-- RADIO -->
          <input
            v-if="mode === 'radio'"
            class="rad"
            type="radio"
            :name="radioName"
            :disabled="isDisabled(it)"
            :checked="String(modelValue) === String(it.key)"
            @change="onRadio(it.key)"
          />

          <!-- CHECKBOX -->
          <input
            v-else
            class="chk"
            type="checkbox"
            :disabled="isDisabled(it)"
            :checked="!!(modelValue as any)?.[it.key]"
            @change="onToggle(it.key, $event)"
          />

          <span class="rowText">
            <!-- STARS (optional) -->
            <span v-if="typeof it.stars === 'number'" class="starsRow" aria-hidden="true">
              <span v-for="n in it.stars" :key="n" class="star">★</span>
            </span>

            <span class="labelText">
              {{ it.label }}
            </span>
          </span>
        </label>

        <div v-if="typeof it.count === 'number'" class="count">{{ it.count }}</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
export type ChecklistItem = {
  key: string;
  label: string;
  count?: number;
  hint?: string;

  /** если задано — рисуем "★ ★ ★ ..." перед label */
  stars?: number;
};

const props = withDefaults(
  defineProps<{
    title?: string;
    subtitle?: string;
    items: ChecklistItem[];

    /** checkbox: map, radio: string */
    modelValue: any;

    mode?: 'checkbox' | 'radio';

    /** чтобы радио-группа работала корректно */
    radioName?: string;

    /** опционально: дизейблить опции с count=0 */
    disableZeroCount?: boolean;
  }>(),
  {
    mode: 'checkbox',
    radioName: 'radio-group',
    disableZeroCount: false,
  }
);

const emit = defineEmits<{
  (e: 'update:modelValue', v: any): void;
}>();

function isDisabled(it: ChecklistItem) {
  return props.disableZeroCount && typeof it.count === 'number' && it.count === 0;
}

function onToggle(key: string, e: Event) {
  const checked = (e.target as HTMLInputElement).checked;
  emit('update:modelValue', { ...(props.modelValue ?? {}), [key]: checked });
}

function onRadio(key: string) {
  emit('update:modelValue', key);
}
</script>

<style scoped>
.section {
  display: flex;
  flex-direction: column;
}

.sectionTitle {
  font-size: 16px;
  line-height: 22px;
  margin-block-end: 12px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
}

.sectionSubtitle {
  font-size: 14px;
  font-weight: 700;
  line-height: 20px;
  margin-block-end: 8px;
  color: var(--bench-text, #2d3137);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.rowDisabled {
  opacity: 0.45;
}

.rowLeft {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
  user-select: none;
}

.rowText {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-family: PTRootUI, Verdana, sans-serif;
}

.labelText {
  font-size: 14px;
  font-weight: 480;
  line-height: 20px;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.count {
  color: #868686;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  margin-inline-start: auto;
  padding-inline-start: 10px;
}

/* checkbox like Отели */
.chk {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid #e5e5e5;
  appearance: none;
  display: grid;
  place-items: center;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  flex: 0 0 auto;
}

.chk:checked {
  border-color: #0e41d2;
  background: #0e41d2;
}

.chk:checked::after {
  content: '';
  width: 10px;
  height: 6px;
  border: 2px solid #fff;
  border-top: 0;
  border-right: 0;
  transform: rotate(-45deg);
  margin-top: -1px;
}

/* radio */
.rad {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #c8c8c8;
  appearance: none;
  display: grid;
  place-items: center;
  background: var(--bench-surface-elevated, #fff);
  cursor: pointer;
  flex: 0 0 auto;
}

.rad:checked {
  border-color: #0e41d2;
}

.rad:checked::after {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #0e41d2;
}

/* stars */
.starsRow {
  display: inline-flex;
  gap: 2px;
  color: #f59e0b;
  font-size: 16px;
  line-height: 1;
}
.star {
  display: inline-block;
}
</style>
