<template>
  <FieldShell>
    <template #label>Направление</template>

    <div class="inputWrap">
      <input
        ref="inputRef"
        class="textInput"
        :placeholder="placeholder"
        :value="inputText"
        @input="onInput"
        @focus="open"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="pickActive()"
        @keydown.esc="close"
      />

      <button v-if="modelValue" class="clearBtn" type="button" @click="clear">×</button>

      <div v-if="isOpen" class="dropdown" @mousedown.prevent>
        <div class="dropdownHead">
          <div class="hint">
            <span v-if="loading">Загрузка…</span>
            <span v-else-if="error">Ошибка: {{ error }}</span>
            <span v-else>Выберите город</span>
          </div>
        </div>

        <div class="list">
          <button
            v-for="(opt, idx) in filtered"
            :key="opt.cityId"
            class="opt"
            type="button"
            :class="{ active: idx === activeIndex }"
            @mouseenter="activeIndex = idx"
            @click="select(opt)"
          >
            <div class="optTitle">{{ opt.cityName }}</div>
            <div class="optSub">{{ opt.countryName }}</div>
          </button>

          <div v-if="!loading && !error && filtered.length === 0" class="empty">
            Ничего не найдено
          </div>
        </div>
      </div>
    </div>
  </FieldShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import FieldShell from './FieldShell.vue';
import type { DestinationOption } from '@/hotels/services/searchDataset';
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent';

const { send } = useHotelTrackEvent();

const props = defineProps<{
  modelValue: DestinationOption | null;
  options: DestinationOption[];
  loading?: boolean;
  error?: string | null;
  placeholder?: string;
  limit?: number;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', v: DestinationOption | null): void;
}>();

const placeholder = computed(() => props.placeholder ?? 'Город, отель или аэропорт');
const limit = computed(() => props.limit ?? 16);

const isOpen = ref(false);
const query = ref('');
const activeIndex = ref(0);

const inputRef = ref<HTMLInputElement | null>(null);

const inputText = computed(() => {
  // если выбрали город — показываем его label, пока не начали печатать новое
  if (!isOpen.value && props.modelValue) return props.modelValue.label;
  return query.value;
});

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  const list = props.options || [];

  if (!q) return list.slice(0, limit.value);

  return list
    .filter((o) => {
      const a = o.label.toLowerCase();
      const b = o.cityName.toLowerCase();
      const c = o.countryName.toLowerCase();
      return a.includes(q) || b.includes(q) || c.includes(q);
    })
    .slice(0, limit.value);
});

function open() {
  isOpen.value = true;
  activeIndex.value = 0;
  // если уже было выбрано — начинаем новый поиск с пустого
  if (props.modelValue) query.value = '';
}

function close() {
  isOpen.value = false;
  activeIndex.value = 0;
  query.value = '';
}

function onInput(e: Event) {
  isOpen.value = true;
  activeIndex.value = 0;
  query.value = (e.target as HTMLInputElement).value;
}

function select(opt: DestinationOption) {
  send(HOTEL_EVENTS.selectCity, {
    cityId: opt.cityId,
    label: opt.label,
    cityName: opt.cityName,
    countryName: opt.countryName,
  });
  emit('update:modelValue', opt);
  close();
}

function clear() {
  emit('update:modelValue', null);
  query.value = '';
  nextTick(() => inputRef.value?.focus());
  open();
}

function move(dir: 1 | -1) {
  if (!isOpen.value) open();
  const max = filtered.value.length - 1;
  if (max < 0) return;
  activeIndex.value = Math.max(0, Math.min(max, activeIndex.value + dir));
}

function pickActive() {
  const opt = filtered.value[activeIndex.value];
  if (opt) select(opt);
}

function onWindowDown(e: MouseEvent) {
  if (!isOpen.value) return;
  const target = e.target as HTMLElement | null;
  if (!target) return;
  const wrap = target.closest('.inputWrap');
  if (!wrap) close();
}

onMounted(() => {
  window.addEventListener('mousedown', onWindowDown, true);
});
onBeforeUnmount(() => {
  window.removeEventListener('mousedown', onWindowDown, true);
});

// если options обновились — сбрасываем активный индекс
watch(
  () => props.options,
  () => {
    activeIndex.value = 0;
    if (isOpen.value) query.value = '';
  },
);
</script>

<style scoped>
.inputWrap {
  position: relative;
  min-width: 0;
}

.textInput {
  border: 0;
  outline: 0;
  font-size: 16px;
  line-height: 20px;
  font-weight: 400;
  color: var(--bench-text, #2d3137);
  padding: 0;
  background: transparent;
  inline-size: 100%;
  font-family: PTRootUI;
}
.textInput::placeholder {
  color: rgba(41, 47, 55, 0.35);
  font-weight: 500;
}

.clearBtn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 0;
  background: rgba(0, 0, 0, 0.06);
  cursor: pointer;
  font-size: 18px;
  line-height: 28px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.75);
}

.dropdown {
  position: absolute;
  left: -10px;
  right: -10px;
  top: calc(100% + 10px);
  background: var(--bench-surface-elevated, #fff);
  border-radius: 14px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.16);
  padding: 8px;
  z-index: 50;
}

.dropdownHead {
  padding: 6px 8px 8px 8px;
}

.hint {
  font-size: 12px;
  font-weight: 600;
  color: var(--bench-text-muted, rgba(45, 49, 55, 0.55));
  font-family: PTRootUI, sans-serif;
}

.list {
  max-height: 240px; /* ✅ скролл списка */
  overflow: auto;
  overscroll-behavior: contain;
  padding-right: 2px;
}

.opt {
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  cursor: pointer;
  padding: 10px 10px;
  border-radius: 12px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.opt:hover,
.opt.active {
  background: rgba(0, 0, 0, 0.06);
}

.optTitle {
  font-size: 14px;
  font-weight: 700;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
}

.optSub {
  font-size: 12px;
  font-weight: 600;
  color: var(--bench-text-muted, rgba(45, 49, 55, 0.55));
  font-family: PTRootUI, sans-serif;
}

.empty {
  padding: 10px 10px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}
</style>
