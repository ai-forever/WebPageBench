<template>
  <div ref="root" class="guestsRoot">
    <!-- Само поле как у тебя (через FieldShell) -->
    <FieldShell as="button" clickable class="guestsField" type="button" @click="toggle">
      <template #label>{{ roomsLabel }} для</template>

      <div class="guValue">{{ guestsLabel }}</div>

      <template #right>
        <div class="guIcon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="nonzero"
              d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
            />
          </svg>
        </div>
      </template>
    </FieldShell>

    <!-- Попап -->
    <div v-show="open" class="popup" role="dialog" aria-label="Выбор постояльцев" @click.stop>
      <div class="inner-popup">
        <div
          v-for="(room, roomIndex) in rooms"
          :key="room.id"
          class="room-form"
        >
          <div class="room-form-inner">
            <div class="room-number-box">
              <div class="room-number">{{ roomIndex + 1 }} номер</div>

              <button
                v-if="rooms.length > 1 && roomIndex > 0"
                type="button"
                class="room-remove"
                @click="removeRoom(roomIndex)"
              >
                Удалить
              </button>
            </div>

            <div class="room-row">
              <!-- Adults -->
              <div class="adult-selector">
                <div class="room-label">Взрослые</div>

                <div class="adult-selector-box">
                  <button
                    type="button"
                    class="counter"
                    :disabled="room.adults <= ADULTS_MIN"
                    @click="decAdults(roomIndex)"
                  >
                    −
                  </button>

                  <div class="adult-count">{{ room.adults }}</div>

                  <button
                    type="button"
                    class="counter"
                    :disabled="room.adults >= ADULTS_MAX"
                    @click="incAdults(roomIndex)"
                  >
                    +
                  </button>
                </div>
              </div>

              <!-- Kids -->
              <div class="kids-selector">
                <div class="room-label">Дети</div>

                <div class="kids-selector-box">
                  <!-- Когда детей нет: большая кнопка "Добавить ребёнка" -->
                  <div v-if="room.kids.length === 0" class="kidAddEmpty">
                    <select
                      v-model="kidDraft[roomIndex]"
                      class="kidSelect"
                      @change="commitKid(roomIndex)"
                    >
                      <option value="" hidden></option>
                      <option v-for="age in ages" :key="age" :value="String(age)">
                        {{ age }} {{ ageWord(age) }}
                      </option>
                    </select>
                    <span class="kidAddEmptyLabel">Добавить ребёнка</span>
                  </div>

                  <!-- Когда дети есть: чипы + квадратный плюс -->
                  <template v-else>
                    <div
                      v-for="(age, kidIndex) in room.kids"
                      :key="`${room.id}-kid-${kidIndex}`"
                      class="kidChip"
                    >
                      <div class="kidChipUnit">
                        <div class="kidChipText">{{ age }} {{ ageWord(age) }}</div>
                        <button
                          type="button"
                          class="kidChipRemove"
                          aria-label="Удалить ребёнка"
                          @click="removeKid(roomIndex, kidIndex)"
                        >
                          <svg fill="#2d3137" height="13" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" width="13" stroke-width="1">
                            <path fill-rule="evenodd" d="M1.293 1.293a1 1 0 0 0 0 1.414l5.303 5.304-5.303 5.303a1 1 0 1 0 1.414 1.414L8.01 9.425l5.304 5.303a1 1 0 0 0 1.414-1.414L9.425 8.01l5.303-5.303a1 1 0 0 0-1.414-1.414L8.01 6.596 2.707 1.293a1 1 0 0 0-1.414 0Z" clip-rule="evenodd"></path>
                          </svg>
                      </button>
                      </div>
                    </div>

                    <div class="kidChip">
                      <div class="addKidModule">
                        <select
                          v-model="kidDraft[roomIndex]"
                          class="kidSelect"
                          @change="commitKid(roomIndex)"
                        >
                          <option value="" hidden></option>
                          <option v-for="age in ages" :key="age" :value="String(age)">
                            {{ age }} {{ ageWord(age) }}
                          </option>
                        </select>
                        <span class="kidPlusIcon">+</span>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="footer-module">
          <div class="footer-box">
            <div class="addRoomBtn" role="button" tabindex="0" @click="addRoom">
              Добавить номер
            </div>
            
            <button type="button" class="doneBtn" @click="onGuestsDone">
              <div class="buttonContent">
                Готово
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import FieldShell from '../Home/FieldShell.vue'
import { HOTEL_EVENTS, useHotelTrackEvent } from '@/hotels/composable/useHotelTrackEvent'
import { useHotelGuests } from '@/hotels/composable/useHotelGuests'

const { send } = useHotelTrackEvent()
const { rooms, roomsCount, guestsCount } = useHotelGuests()

const ADULTS_MIN = 1
const ADULTS_MAX = 9
const KIDS_MAX = 6 // чтобы UI не расползался, можешь поменять

const open = ref(false)
const root = ref<HTMLElement | null>(null)

// черновик для select (по индексу комнаты)
const kidDraft = ref<string[]>(rooms.value.map(() => ''))

const ages = Array.from({ length: 18 }, (_, i) => i)

function pluralRu(n: number, one: string, few: string, many: string) {
  const n10 = n % 10
  const n100 = n % 100
  if (n10 === 1 && n100 !== 11) return one
  if (n10 >= 2 && n10 <= 4 && (n100 < 12 || n100 > 14)) return few
  return many
}

function ageWord(age: number) {
  // 0 лет, 1 год, 2-4 года, 5-… лет
  return pluralRu(age, 'год', 'года', 'лет')
}

const roomsLabel = computed(() => {
  const n = roomsCount.value
  return `${n} ${pluralRu(n, 'номер', 'номера', 'номеров')}`
})

const guestsLabel = computed(() => {
  const n = guestsCount.value
  return `${n} ${pluralRu(n, 'гость', 'гостя', 'гостей')}`
})

function ensureDraftSize() {
  // подгоняем kidDraft под текущее количество комнат
  if (kidDraft.value.length < rooms.value.length) {
    while (kidDraft.value.length < rooms.value.length) kidDraft.value.push('')
  } else if (kidDraft.value.length > rooms.value.length) {
    kidDraft.value.splice(rooms.value.length)
  }
}

function toggle(e: MouseEvent) {
  e.stopPropagation()
  open.value = !open.value
}

function close() {
  open.value = false
}

function onDocClick(e: MouseEvent) {
  if (!open.value) return
  const el = root.value
  if (!el) return
  if (el.contains(e.target as Node)) return
  close()
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))

function addRoom() {
  rooms.value.push({ id: crypto.randomUUID(), adults: 2, kids: [] })
  ensureDraftSize()
}

function removeRoom(roomIndex: number) {
  rooms.value.splice(roomIndex, 1)
  ensureDraftSize()
}

function incAdults(roomIndex: number) {
  const r = rooms.value[roomIndex]
  if (!r) return
  if (r.adults >= ADULTS_MAX) return
  r.adults += 1
}

function decAdults(roomIndex: number) {
  const r = rooms.value[roomIndex]
  if (!r) return
  if (r.adults <= ADULTS_MIN) return
  r.adults -= 1
}

function commitKid(roomIndex: number) {
  const r = rooms.value[roomIndex]
  if (!r) return

  const raw = kidDraft.value[roomIndex]
  const age = raw === '' ? NaN : Number(raw)
  kidDraft.value[roomIndex] = '' // сброс

  if (Number.isNaN(age)) return
  if (r.kids.length >= KIDS_MAX) return

  r.kids.push(age)
}

function removeKid(roomIndex: number, kidIndex: number) {
  const r = rooms.value[roomIndex]
  if (!r) return
  r.kids.splice(kidIndex, 1)
}

function onGuestsDone() {
  open.value = false
  send(HOTEL_EVENTS.selectGuests, {
    rooms: rooms.value.map((r) => ({ adults: r.adults, kids: [...r.kids] })),
    roomsCount: roomsCount.value,
    guestsCount: guestsCount.value,
  })
}
</script>

<style scoped>
.addKidModule {
  position: relative;
  box-sizing: border-box;

  min-inline-size: auto;

  /* padding: 4px 4px; */
  padding: 0 12px;

  border: 1.5px solid #e5e5e5;
  border-radius: 12px;
}

.kidChipText {
  display: inline-block;
  white-space: nowrap;

  font-size: 16px;
  font-weight: 500;
  line-height: 1.231;
  color: var(--bench-text, #2d3137);

  font-family: 'PTRootUI', Verdana, sans-serif;
}

.kidChipUnit {
  background-color: var(--bench-primary-light, #f4f4f4);
  border-radius: 6px;

  align-items: center;
  block-size: 36px;
  box-sizing: border-box;
  display: flex;
  font-size: 16px;
  font-weight: 500;
  padding-block-end: 8px;
  padding-block-start: 8px;
  padding-inline-end: 0;
  padding-inline-start: 12px;
}

button {
  background: none;
}

.buttonContent {
  padding: 4px;
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  color: #FFF;
}

.doneBtn {
  margin: 8px;
  padding: 0 12px;

  background-color: #0e41d2;
  border: 1px solid transparent;
  border-radius: 12px;
  cursor: pointer;

  inline-size: 100%;

  block-size: 48px;
  font-size: 16px;
  line-height: 20px;
  min-inline-size: 48px;

  align-items: center;
  box-sizing: border-box;
  color: #FFF;
  display: inline-flex;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-weight: 500;
  justify-content: center;
  min-inline-size: 40px;
  position: relative;
  text-decoration: none;
  transition: background-color 0.16s ease, color 0.16s ease, box-shadow 0.16s ease;
  user-select: none;
}

.addRoomBtn::before {
  content: '+';
  font-size: 26px !important;
  inset-block-start: 0 !important;
  inset-inline-start: 0 !important;
  line-height: 1em !important;
  position: absolute;

  cursor: pointer;
}

.addRoomBtn {
  cursor: pointer;
  margin: 8px;

  align-items: center;
  color: #0e41d2;
  display: inline-flex;
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-weight: 500;
  inline-size: 100%;
  line-height: 22px;
  padding-inline-start: 18px;
  position: relative;
  user-select: none;
}

.footer-box {
  padding: 0 8px 8px;
  align-items: center;
  display: flex;
}

.footer-module {
  background: var(--bench-surface-elevated, #fff);

  inset-block-end: 0;
  inset-inline: 0;
  position: sticky;
  z-index: 12px;
}

/* контейнер вокруг FieldShell + popup */
.guestsRoot {
  position: relative;
  z-index: 999999999999999999999999;
}

/* значения как у тебя */
.guValue {
  font-size: 16px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: PTRootUI, sans-serif;
}

.guIcon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  color: rgba(45, 49, 55, 0.55);
  flex: 0 0 auto;
  pointer-events: none;
}

/* POPUP */
.popup {
  width: 370px;
  padding: 0;
  background-color: var(--bench-surface-elevated, #fff);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(45, 49, 55, 0.3);
  max-block-size: 500px;
  overflow-y: auto;
  box-sizing: border-box;
  position: absolute;
  z-index: 2200;

  /* позиция под полем */
  top: calc(100% + 8px);
  right: 0;
}

.inner-popup {
  position: relative;
}

.room-form {
  padding: 20px;
  margin-block-end: -24px;
}

.room-form-inner {
  border-block-end: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  padding-block-end: 16px;
}

.room-number-box {
  display: flex;
  align-items: center;
  flex-grow: 1;
  justify-content: space-between;
  margin-block-end: 12px;
}

.room-number {
  font-size: 20px;
  font-weight: 700;
  line-height: 24px;
  font-family: PTRootUI, sans-serif;
  color: var(--bench-text, #2d3137);
}

.room-remove {
  cursor: pointer;
  background: none;
  border: 0;
  color: #ce2121;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, sans-serif;
}

.room-row {
  display: flex;
}

.room-label {
  font-size: 12px;
  font-weight: 500;
  inline-size: 100%;
  line-height: 15px;
  margin-block-end: 8px;
  font-family: PTRootUI, sans-serif;
  color: var(--bench-text, #2d3137);
}

/* Adults */
.adult-selector {
  display: flex;
  flex-direction: column;
  margin-inline-end: 20px;
}

.adult-selector-box {
  border-radius: 12px;
  box-shadow: 0 0 0 1px #e5e5e5;
  align-items: center;
  block-size: 36px;
  box-sizing: border-box;
  display: flex;
  font-size: 16px;
  font-weight: 500;
  inline-size: 93px;
  justify-content: space-between;
  line-height: 20px;
}

.adult-count {
  display: inline-block;
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, sans-serif;
  color: var(--bench-text, #2d3137);
}

.counter {
  cursor: pointer;
  background: none;
  border: 0;
  block-size: 36px;
  inline-size: 36px;
  box-sizing: border-box;
  color: var(--bench-text, #2d3137);
  font-size: 24px;
  line-height: 30px;
  overflow: hidden;
  font-family: PTRootUI, sans-serif;
  font-weight: 480;
}

.counter:disabled {
  opacity: 0.35;
  cursor: default;
}

/* Kids */
.kids-selector {
  display: flex;
  flex: 1;
  flex-direction: column;
}

.kids-selector-box {
  display: flex;
  flex-grow: 1;
  flex-wrap: wrap;
}

/* общий стиль для скрытого select поверх "кнопки" */
.kidSelect {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;

  font-size: 13px;
  line-height: 1.231;
  font-family: 'PTRootUI', Verdana, sans-serif;
  font-weight: 480;

  border: 1px solid #e5e5e5;
  border-radius: 12px;
}

/* state: no kids -> большая кнопка */
.kidAddEmpty {
  position: relative;
  inline-size: 100%;
  min-block-size: 36px;
  border-radius: 12px;
  box-shadow: 0 0 0 1px #e5e5e5;
  background: var(--bench-surface-elevated, #fff);
  display: flex;
  align-items: center;
  padding: 0 16px;
}

.kidAddEmptyLabel {
  font-size: 16px;
  font-weight: 500;
  line-height: 20px;
  font-family: PTRootUI, sans-serif;
  color: var(--bench-text, #2d3137);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* chips */
.kidChip {
  margin-block-end: 8px;
  margin-inline-end: 8px;

  /* display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background: #f4f4f4;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, sans-serif;
  font-size: 20px;
  font-weight: 500;
  line-height: 24px; */
}

.kidChipRemove {
  cursor: pointer;
  background: none;
  border: 0;

  block-size: 36px;
  color: #868686;

  inline-size: 26px;
  padding-block-start: 2px;
  padding-inline-end: 5px;

  font-size: 13px;
  line-height: 1.231;
  font-family: 'PTRootUI', Verdana, sans-serif;
  font-weight: 480;
}

/* плюс-кнопка */
.kidAddPlus {
  position: relative;
  inline-size: 78px;
  block-size: 56px;
  border-radius: 16px;
  box-shadow: 0 0 0 2px #0e41d2; /* как на скрине (синий контур) */
  background: var(--bench-surface-elevated, #fff);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kidPlusIcon {
  font-size: 36px;
  line-height: 36px;
  font-weight: 700;
  color: rgba(45, 49, 55, 0.55);
  font-family: PTRootUI, sans-serif;
}

/* footer */
.footer {
  display: flex;
  justify-content: space-between;
  padding: 20px;
  gap: 16px;
}
</style>
