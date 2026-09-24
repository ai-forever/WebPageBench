<template>
  <div class="dp" data-testid="datepicker-calendar">
    <!-- left: months list -->
    <div class="months">
      <div ref="monthsScrollRef" class="monthsScroll" @scroll="onMonthsScroll">
        <div class="underlay" :style="{ top: `${underlayTop}px`, height: `${underlayH}px` }"></div>

        <button
          v-for="(m, i) in months"
          :key="m.key"
          :ref="(el) => setMonthItemEl(i, el)"
          class="monthItem"
          type="button"
          @click="onMonthClick(i)"
        >
          <div class="mTitle">{{ m.title }}</div>
          <div v-if="m.showYear" class="mYear">{{ m.year }}</div>
        </button>
      </div>
    </div>

    <!-- right: grid -->
    <div class="grid">
      <div class="dow">
        <div v-for="d in dows" :key="d" class="dowCell">{{ d }}</div>
      </div>
      <div class="sep"></div>

      <div ref="gridScrollRef" class="gridScroll" @scroll="onGridScroll">
        <template v-for="(m, idx) in months" :key="m.key">
          <div v-if="m.isJanuary" class="yearLabel">{{ m.year }}</div>

          <section class="monthBlock" :data-month-index="idx" :ref="(el) => setMonthEl(idx, el)">
            <div class="monthTitle">{{ m.titleFull }}</div>

            <div class="weeks">
              <div v-for="(week, wi) in m.weeks" :key="`${m.key}-w${wi}`" class="week">
                <div v-for="(day, di) in week" :key="`${m.key}-d${wi}-${di}`" class="dayCell">
                  <button
                    v-if="day"
                    class="dayBtn"
                    type="button"
                    :disabled="isDisabled(day)"
                    :class="dayClass(day)"
                    @mouseenter="onHover(day)"
                    @mouseleave="onHover(null)"
                    @click="pick(day)"
                  >
                    {{ day.getDate() }}
                  </button>
                  <div v-else class="dayBlank"></div>
                </div>
              </div>
            </div>
          </section>
        </template>

        <div class="bottomFade"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from 'vue';

type ActiveField = 'start' | 'end';

const props = defineProps<{
  start: Date | null;
  end: Date | null;
  minDate: Date;
  monthsAhead: number;
  activeField: ActiveField;
}>();

const emit = defineEmits<{
  (e: 'update:start', v: Date | null): void;
  (e: 'update:end', v: Date | null): void;
  (e: 'done'): void;
}>();

const dows = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];

const monthNames = [
  'Январь','Февраль','Март','Апрель','Май','Июнь',
  'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
];

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}
function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}
function isBefore(a: Date, b: Date) {
  return startOfDay(a).getTime() < startOfDay(b).getTime();
}
function inRange(d: Date, a: Date, b: Date) {
  const t = startOfDay(d).getTime();
  const t1 = startOfDay(a).getTime();
  const t2 = startOfDay(b).getTime();
  return t >= Math.min(t1, t2) && t <= Math.max(t1, t2);
}
function dowMon0(d: Date) {
  return (d.getDay() + 6) % 7; // Mon=0..Sun=6
}
function daysInMonth(y: number, m: number) {
  return new Date(y, m + 1, 0).getDate();
}

function buildWeeks(y: number, m: number) {
  const first = new Date(y, m, 1);
  const lead = dowMon0(first);
  const dim = daysInMonth(y, m);

  const cells: (Date | null)[] = [];
  for (let i = 0; i < lead; i++) cells.push(null);
  for (let d = 1; d <= dim; d++) cells.push(new Date(y, m, d));

  const tail = (7 - (cells.length % 7)) % 7;
  for (let i = 0; i < tail; i++) cells.push(null);

  const weeks: (Date | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

const today = startOfDay(new Date());
const base = computed(() => startOfDay(props.minDate ?? today));

const months = computed(() => {
  const start = new Date(base.value.getFullYear(), base.value.getMonth(), 1);
  const res: any[] = [];
  for (let i = 0; i < props.monthsAhead; i++) {
    const d = new Date(start.getFullYear(), start.getMonth() + i, 1);
    const y = d.getFullYear();
    const m = d.getMonth();
    const title = monthNames[m];
    res.push({
      key: `${y}-${m}`,
      year: y,
      month: m,
      title,
      titleFull: `${title} ${y}`,
      showYear: m === 0 || i === 0,
      isJanuary: m === 0,
      weeks: buildWeeks(y, m),
    });
  }
  return res;
});

const hover = ref<Date | null>(null);

function isDisabled(d: Date) {
  return startOfDay(d).getTime() < startOfDay(props.minDate).getTime();
}
function onHover(d: Date | null) {
  hover.value = d;
}

function pick(d: Date) {
  const day = startOfDay(d);

  if (props.start && props.end) {
    emit('update:start', day);
    emit('update:end', null);
    return;
  }

  if (!props.start) {
    emit('update:start', day);
    emit('update:end', null);
    return;
  }

  if (!props.end) {
    if (isBefore(day, props.start)) {
      emit('update:end', props.start);
      emit('update:start', day);
    } else {
      emit('update:end', day);
    }
    emit('done');
  }
}

function dayClass(d: Date) {
  const cls: Record<string, boolean> = {};
  const s = props.start ? startOfDay(props.start) : null;
  const e = props.end ? startOfDay(props.end) : null;
  const h = hover.value ? startOfDay(hover.value) : null;

  const isS = !!s && isSameDay(d, s);
  const isE = !!e && isSameDay(d, e);

  let rangeA: Date | null = null;
  let rangeB: Date | null = null;

  if (s && e) {
    rangeA = s;
    rangeB = e;
  } else if (s && h && !e) {
    rangeA = s;
    rangeB = h;
  }

  const inR = rangeA && rangeB ? inRange(d, rangeA, rangeB) : false;

  cls.selected = isS || isE;
  cls.inRange = inR && !(isS || isE);
  cls.edgeStart = isS;
  cls.edgeEnd = isE;

  if (rangeA && rangeB && inR) {
    const left = new Date(d); left.setDate(d.getDate() - 1);
    const right = new Date(d); right.setDate(d.getDate() + 1);

    const inLeft = inRange(left, rangeA, rangeB);
    const inRight = inRange(right, rangeA, rangeB);

    cls.withLeftRadius = !inLeft;
    cls.withRightRadius = !inRight;
  }

  const hoverDay = !!h && isSameDay(d, h) && !isDisabled(d);

  cls.hoverStart = !s && !e && hoverDay;
  cls.hoverEnd = !!s && !e && hoverDay && !isS;


  if (isS && isE) {
    cls.edgeStart = true;
    cls.edgeEnd = true;
  }

  return cls;
}

/** refs */
const monthsScrollRef = ref<HTMLElement | null>(null);
const gridScrollRef = ref<HTMLElement | null>(null);

const monthItemEls = ref<HTMLElement[]>([]);
function setMonthItemEl(i: number, el: any) {
  if (el && el instanceof HTMLElement) monthItemEls.value[i] = el;
}

const monthEls = ref<HTMLElement[]>([]);
function setMonthEl(i: number, el: any) {
  if (el && el instanceof HTMLElement) monthEls.value[i] = el;
}

/** active month + underlay */
const activeMonthIndex = ref(0);
const underlayTop = ref(0);
const underlayH = ref(0);

function updateUnderlay() {
  const el = monthItemEls.value[activeMonthIndex.value];
  if (!el) return;
  underlayTop.value = el.offsetTop;
  underlayH.value = el.offsetHeight;
}

function ensureMonthVisible(idx: number) {
  const sc = monthsScrollRef.value;
  const el = monthItemEls.value[idx];
  if (!sc || !el) return;

  const pad = 8;
  const top = el.offsetTop;
  const bottom = top + el.offsetHeight;

  const viewTop = sc.scrollTop;
  const viewBottom = viewTop + sc.clientHeight;

  if (top < viewTop + pad) {
    sc.scrollTo({ top: Math.max(0, top - pad), behavior: 'smooth' });
  } else if (bottom > viewBottom - pad) {
    sc.scrollTo({ top: Math.max(0, bottom - sc.clientHeight + pad), behavior: 'smooth' });
  }
}

function calcActiveMonthIndex(scrollTop: number) {
  const threshold = 120;
  let active = 0;
  for (let i = 0; i < monthEls.value.length; i++) {
    const el = monthEls.value[i];
    if (!el) continue;
    if (el.offsetTop - threshold <= scrollTop) active = i;
    else break;
  }
  return active;
}

function syncActiveFromGrid() {
  const g = gridScrollRef.value;
  if (!g) return;

  const idx = calcActiveMonthIndex(g.scrollTop);
  if (idx !== activeMonthIndex.value) {
    activeMonthIndex.value = idx;
    nextTick(() => {
      updateUnderlay();
      ensureMonthVisible(idx); // правый скролл подводит левый при необходимости
    });
  } else {
    updateUnderlay();
  }
}

function onGridScroll() {
  syncActiveFromGrid();
}
function onMonthsScroll() {
  // левый скролл независим
}

async function scrollToMonth(i: number) {
  await nextTick();
  const g = gridScrollRef.value;
  const el = monthEls.value[i];
  if (!g || !el) return;
  g.scrollTo({ top: el.offsetTop, behavior: 'smooth' });
}

function onMonthClick(i: number) {
  activeMonthIndex.value = i;
  nextTick(() => {
    updateUnderlay();
    ensureMonthVisible(i);
  });
  scrollToMonth(i);
}

function onResize() {
  updateUnderlay();
  syncActiveFromGrid();
}

function monthIndexFor(d: Date) {
  const t = startOfDay(d);
  return months.value.findIndex((m) => m.year === t.getFullYear() && m.month === t.getMonth());
}

function jumpToMonth(idx: number) {
  if (idx < 0) return;
  const g = gridScrollRef.value;
  const el = monthEls.value[idx];
  if (!g || !el) return;
  g.scrollTop = el.offsetTop;
  activeMonthIndex.value = idx;
}

onMounted(() => {
  nextTick(() => {
    const focus = props.start ?? props.minDate;
    if (focus) jumpToMonth(monthIndexFor(focus));
    updateUnderlay();
    syncActiveFromGrid();
  });
  window.addEventListener('resize', onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize);
});

watch(
  () => [props.start?.getTime?.(), props.end?.getTime?.()],
  () => nextTick(() => syncActiveFromGrid()),
);
</script>

<style scoped>
/* чтобы wheel не “протекал” в body при достижении края */
.monthsScroll,
.gridScroll {
  overscroll-behavior: contain;
}

/* dp растягивается под заданный размер родителя (.popup) */
.dp {
  display: grid;
  grid-template-columns: 165px 1fr;
  width: 100%;
  height: 100%;
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

/* КРИТИЧНО: разрешаем grid-детям сжиматься по высоте (иначе overflow не работает) */
.months,
.grid {
  min-height: 0;
}

/* LEFT */
.months {
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  background: var(--bench-surface-elevated, #fff);
  min-width: 0;
}

.monthsScroll {
  position: relative;
  height: 100%;
  overflow: auto;
  padding: 8px 0;
}

.underlay {
  position: absolute;
  left: 10px;
  right: 10px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.06);
  pointer-events: none;
  transition: top 120ms ease, height 120ms ease;
}

.monthItem {
  width: 100%;
  padding: 10px 16px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
  position: relative;
  z-index: 1;
}

.mTitle {
  font-size: 16px;
  line-height: 1.231;
  font-weight: 500;
  color: #292f37;
  font-family: PTRootUI, sans-serif;
}

.mYear {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.6;
  line-height: 1.231;
  color: #292f37;
  font-family: PTRootUI, sans-serif;
}

/* RIGHT */
.grid {
  display: grid;
  grid-template-rows: auto 1px 1fr;
  min-width: 0;
}

.dow {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: 12px 14px 8px 14px;
  background: var(--bench-surface-elevated, #fff);
  z-index: 2;
}

.dowCell {
  font-size: 14px;
  font-weight: 400;
  text-transform: uppercase;
  text-align: center;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
}

.sep {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
}

.gridScroll {
  min-height: 0; /* важно для 1fr */
  overflow: auto;
  padding: 10px 14px 18px 14px;
  position: relative;
}

.yearLabel {
  font-size: 20px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.55);
  text-align: end;
  font-family: PTRootUI, sans-serif;
}

.monthBlock {
  margin-bottom: 18px;
}

.monthTitle {
  font-size: 20px;
  font-weight: 700;
  text-transform: capitalize;
  margin: 8px 0 10px 0;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
}

.weeks {
  display: grid;
  row-gap: 6px;
}

.week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  column-gap: 0;
}

.dayCell {
  height: 32px;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}

.dayBlank {
  width: 100%;
  height: 100%;
}

.dayBtn {
  width: 100%;
  height: 100%;
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  font-weight: 400;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
  display: grid;
  place-items: center;
  border-radius: 0;
}

.dayBtn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.dayBtn.inRange {
  background: rgba(0, 0, 0, 0.05);
}

.dayBtn.selected {
  background: #0e41d2;
  color: #fff;
}

.dayBtn.hoverStart,
.dayBtn.hoverEnd {
  background: #0e41d2;
  color: #fff;
  border-radius: 3px; /* можно убрать, если не надо */
}



.dayBtn.withLeftRadius,
.dayBtn.edgeStart {
  border-top-left-radius: 3px;
  border-bottom-left-radius: 3px;
}

.dayBtn.withRightRadius,
.dayBtn.edgeEnd {
  border-top-right-radius: 3px;
  border-bottom-right-radius: 3px;
}

.bottomFade {
  position: sticky;
  bottom: 0;
  height: 18px;
  background: linear-gradient(to bottom, rgba(255,255,255,0), rgba(255,255,255,1));
  pointer-events: none;
}
</style>
