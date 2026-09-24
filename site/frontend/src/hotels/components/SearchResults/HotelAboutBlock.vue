<template>
  <section v-if="about" class="About">
    <div class="shell">
      <div class="titleRow">
        <h3 class="cardTitle">{{ about.title ?? 'Описание отеля' }}</h3>
      </div>

      <div class="content">
        <!-- LEFT -->
        <div class="left">
          <div v-for="s in visibleSections" :key="s.id" class="desc">
            <p class="descTitle">
              {{ s.title }}
            </p>

            <p v-for="(p, i) in s.paragraphs" :key="s.id + '-' + i" class="descParagraph">
              {{ p }}
            </p>
          </div>

          <div v-show="expanded" class="spoilered">
            <div v-for="s in spoilerSections" :key="s.id" class="desc">
              <p class="descTitle" :class="`descTitle--${s.id}`">
                {{ s.title }}
              </p>

              <p v-for="(p, i) in s.paragraphs" :key="s.id + '-' + i" class="descParagraph">
                {{ p }}
              </p>
            </div>
          </div>

          <div class="spoiler">
            <button class="spoilerBtn" type="button" @click="expanded = !expanded">
              <svg
                class="spoilerArrow"
                :class="{ open: expanded }"
                width="16"
                height="16"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="nonzero"
                  d="M10.908 14.623l6.139-6.14c.5-.499.5-1.315 0-1.815l-.172-.174a1.29 1.29 0 0 0-1.817 0L10 11.553l-5.06-5.06a1.288 1.288 0 0 0-1.814 0l-.173.175c-.5.5-.5 1.316 0 1.816l6.14 6.139a1.288 1.288 0 0 0 1.815 0"
                />
              </svg>

              {{ expanded ? (about.collapseText ?? 'Свернуть описание') : (about.expandText ?? 'Развернуть описание') }}
            </button>
          </div>
        </div>

        <!-- RIGHT -->
        <div class="facts" v-if="about.facts?.items?.length" v-show="expanded">
          <p class="factsTitle">{{ about.facts.title ?? 'Факты об отеле' }}</p>

          <div class="factsList">
            <div v-for="item in about.facts.items" :key="item.key" class="fact">
              <p class="factSubtitle">{{ item.label }}</p>

              <div class="factValue">
                <!-- value: string -->
                <template v-if="typeof item.value === 'string'">
                  {{ item.value }}
                </template>

                <!-- value: string[] -->
                <template v-else>
                  <div
                    v-for="(line, idx) in item.value"
                    :key="item.key + '-' + idx"
                    class="valueLine"
                  >
                    <div v-if="idx === 0" class="valueLineRow">
                      <div class="valueLineText">{{ line }}</div>
                    
                      <button
                        v-if="item.hint"
                        type="button"
                        class="hintBtn"
                        :title="item.hint"
                        aria-label="hint"
                      >
                        <svg class="HintIcon" fill="none" height="22" viewBox="0 0 22 22" width="22">
                          <rect x="3" y="3" width="16" height="16" rx="4"></rect>
                          <path
                            d="M11 6c-.555 0-1.004.459-1.004 1.025 0 .566.45 1.025 1.004 1.025.555 0 1.005-.46 1.005-1.025C12.005 6.459 11.555 6 11 6ZM10.265 13.831H9V15h4v-1.169h-1.265V9.155H9v1.17h1.265v3.506Z"
                          ></path>
                        </svg>
                      </button>
                    </div>
                  
                    <div v-else class="valueLineText">
                      {{ line }}
                    </div>
                  </div>
                </template>

              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

type AboutSection = {
  id: string;
  title: string;
  paragraphs: string[];
  spoiler?: boolean;
};

type FactItem = {
  key: string;
  label: string;
  value: string | string[];
  hint?: string;
};

type AboutBlock = {
  title?: string;
  expandText?: string;
  collapseText?: string;
  sections: AboutSection[];
  facts?: {
    title?: string;
    items: FactItem[];
  };
};

type HotelWithAbout = {
  id: string;
  aboutBlock?: AboutBlock;
};

const props = defineProps<{ hotel: HotelWithAbout }>();

const about = computed(() => props.hotel.aboutBlock ?? null);

// на скрине блок раскрыт -> делаем по умолчанию expanded=true
const expanded = ref(true);

const visibleSections = computed(() =>
  (about.value?.sections ?? []).filter(s => !s.spoiler)
);

const spoilerSections = computed(() =>
  (about.value?.sections ?? []).filter(s => s.spoiler)
);

</script>

<style scoped>
.valueLine {
  display: block;
}

.valueLine + .valueLine {
  margin-top: 4px;
}

.valueLineRow {
  display: flex;
  align-items: center;
  gap: 8px;
}

.valueLineText {
  display: block;
}

.shell {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 16px;
  box-shadow: 0 12px 20px rgba(0, 0, 0, 0.06);
  font-family: PTRootUI, Verdana, sans-serif;
  padding: 24px;
}

.titleRow {
  margin-bottom: 16px;
}

.cardTitle {
  margin: 0;
  font-size: 24px;
  line-height: 30px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.content {
  display: flex;
  gap: 36px;
  align-items: flex-start;
}

/* left */
.left {
  flex: 1;
  min-width: 0;
}

.desc {
  /* margin-top: 18px; */
  margin-block-end: 20px;
}

.descTitle {
  font-size: 16px;
  font-weight: 700;
  line-height: 22px;
  margin-block-end: 12px;
  padding-inline-start: 32px;
  position: relative;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.descTitle::before {
  background-size: contain;
  background-repeat: no-repeat;
  block-size: 20px;
  inline-size: 25px;
  content: "";
  position: absolute;
  top: -2px;
  left: 0;
}

.descTitle--room::before {
  background-image: url(/hotels/cdn/inrooms.1d6a7b68.svg);
}

/* если вдруг прилетит неизвестный id — дефолт как “в номере” */
.descTitle::before {
  background-image: url(/hotels/cdn/inrooms.1d6a7b68.svg);
}

.HintIcon {
  display: block;
  flex-shrink: 0;
  --icon-color: #868686;
  --bg-color: var(--bench-text, #2d3137);
  --bg-opacity: 0.04;
}

:deep(.HintIcon rect) {
  fill: var(--bg-color);
  opacity: var(--bg-opacity);
  transition: fill .16s ease, opacity .16s ease;
}

:deep(.HintIcon path) {
  fill: var(--icon-color);
  transition: fill .16s ease, opacity .16s ease;
}

/* .descIcon {
  display: inline-flex;
  color: var(--bench-text, #2d3137);
  opacity: 0.9;
} */

.descParagraph {
  /* margin: 0 0 10px; */
  font-size: 14px;
  line-height: 20px;
  font-weight: 400;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.spoilered {
  margin-top: 18px;
}

.spoiler {
  margin-top: 14px;
}

.spoilerBtn {
  border: 0;
  background: none;
  padding: 0;
  cursor: pointer;
  color: #0e41d2;
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: PTRootUI, Verdana, sans-serif;
}

.spoilerArrow {
  transition: transform 160ms ease;
  transform: rotate(0deg); /* в раскрытом состоянии “вверх” */
}

.spoilerArrow.open {
  transform: rotate(180deg);
}

/* right facts */
.facts {
  width: 340px;
  flex-shrink: 0;
}

.factsTitle {
  margin: 0 0 12px;
  font-size: 16px;
  line-height: 22px;
  font-weight: 800;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.fact{
  margin-top: 12px;
}

.factSubtitle {
  margin: 0 0 5px;
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  color: #868686;
  font-family: PTRootUI, Verdana, sans-serif;
}

.factValue {
  font-size: 14px;
  margin-block-end: 8px;
  line-height: 20px;
  font-weight: 500;
  color: var(--bench-text, #2d3137);
  font-family: PTRootUI, Verdana, sans-serif;
}

.valueLine {
  /* display: inline-flex; */
  align-items: center;
  gap: 8px;
}

.hintBtn {
  border: 0;
  background: none;
  padding: 0;
  cursor: help;
  display: inline-flex;
}

.hintIcon rect {
  stroke: rgba(45, 49, 55, 0.25);
}
.hintIcon path {
  fill: rgba(45, 49, 55, 0.75);
}

@media (max-width: 980px) {
  .content {
    flex-direction: column;
  }
  .facts {
    width: 100%;
  }
}
</style>
