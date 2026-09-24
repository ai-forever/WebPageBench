<template>
  <div v-if="isOpen" class="zenemailcollectorV2">
    <div class="zenemailcollectorV2-close" role="button" tabindex="0" @click="close" @keydown.enter="close" />

    <div class="zenemailcollectorV2-content">
      <div class="zenemailcollectorV2-inner">
        <div class="zenemailcollectorV2-image" />

        <div class="zenemailcollectorV2-form-wrap">
          <div class="zenemailcollectorV2-title">Путешествуйте выгоднее!</div>
          <div class="zenemailcollectorV2-subtitle">Узнавайте первыми о выгодных ценах и спецпредложениях.</div>

          <form class="zenemailcollectorV2-form" @submit.prevent="submit">
            <div class="zenemailcollectorV2-form-inner">
              <div class="zenemailcollectorV2-field-wrapper">
                <div class="zenemailcollectorV2-field">
                  <ZenFormInput
                    v-model="email"
                    id="email"
                    name="email"
                    label="Электронная почта"
                    placeholder="example@mail.ru"
                    type="email"
                  />
                </div>
              </div>

              <div class="zenemailcollectorV2-submit">
                <button class="zenemailcollectorV2-button button-view-primary button-size-l" type="submit">
                  Подписаться
                </button>
              </div>
            </div>

            <div class="zenemailcollectorV2-checkbox-wrapper">
              <div class="zenemailcollectorV2-checkbox">
                <ZenCheckbox v-model="agreed">
                  <span class="zencheckbox-text">
                    Я
                    <a
                      target="_blank"
                      class="zenemailcollectorV2-policy-link link"
                      href="/hotels/cdn/privacy-policy-advertisement.bin"
                      rel="noreferrer"
                    >
                      согласен
                    </a>
                    получать рассылки с новостями, рекламой и спецпредложениями
                  </span>
                </ZenCheckbox>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import ZenFormInput from "./ZenFormInput.vue";
import ZenCheckbox from "./ZenCheckbox.vue";

const isOpen = ref(true);
const email = ref("");
const agreed = ref(false);

function close() {
  isOpen.value = false;
}

function submit() {
  // пока просто заглушка — подключишь позже
  // тут можно валидировать email + agreed
  console.log({ email: email.value, agreed: agreed.value });
}
</script>

<style scoped>
/* локальные дефолты переменных (чтобы компонент выглядел так же, даже если global vars еще нет) */
.zenemailcollectorV2 {
  --palette-white: var(--bench-surface-elevated, #ffffff);
  --text: var(--bench-text, #2d3137);
  --link: #0e41d2;
  --button-primary-bg: #0e41d2;

  --box-bg: var(--bench-surface-elevated, #ffffff);
  --box-border: rgba(45, 49, 55, 0.25);
  --box-on-typo: #ffffff;

  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

/* крестик */
.zenemailcollectorV2-close {
  height: 20px;
  width: 20px;
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 3;

  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20'%3E%3Cpath fill='%23c8c8c8' d='M11.6 10l5.1-5.2a1.1 1.1 0 00-1.5-1.6L10 8.4 4.8 3.2a1.1 1.1 0 00-1.6 0 1.1 1.1 0 000 1.6L8.4 10l-5.2 5.2a1.1 1.1 0 000 1.6 1.1 1.1 0 001.6 0l5.2-5.2 5.2 5.2a1.1 1.1 0 001.5-1.6L11.6 10z'/%3E%3C/svg%3E");
  background-position: center;
  background-repeat: no-repeat;
  cursor: pointer;
}

.zenemailcollectorV2-content {
  background-color: var(--palette-white);
}

.zenemailcollectorV2-inner {
  display: flex;
  position: relative;
  background-color: var(--palette-white);
}

/* картинка слева */
.zenemailcollectorV2-image {
  min-width: 327px;
  background-image: url("/hotels/cdn/island.png");
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
}

/* правая часть */
.zenemailcollectorV2-form-wrap {
  width: 100%;
  padding: 32px 40px;
}

.zenemailcollectorV2-title {
  font-family: "Spoof", system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  font-size: 32px;
  font-weight: 500;
  margin-bottom: 12px;
  color: var(--text);
}

.zenemailcollectorV2-subtitle {
  font-size: 16px;
  margin-bottom: 28px;
  color: var(--text);
}

/* форма */
.zenemailcollectorV2-form-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
}

.zenemailcollectorV2-field-wrapper {
  flex: 1 0 25%;
  min-width: 300px;
}

/* submit */
.zenemailcollectorV2-submit {
  flex: 0 0 280px;
  min-width: 240px;
}

.zenemailcollectorV2-button {
  width: 100%;
  margin-left: 12px;

  font-size: 22px;
  line-height: 26px;
  min-height: 56px;
}

/* общие стили кнопки */
.button-size-l {
  padding: 14px 24px;
}
.button-view-primary {
  background-color: var(--button-primary-bg);
  border-radius: 12px;
  border: 1px solid transparent;
  cursor: pointer;
  text-align: center;
  color: #fff;
}
button {
  background: none;
  border: 0;
  cursor: pointer;
}

/* чекбокс блок */
.zenemailcollectorV2-checkbox-wrapper {
  margin-top: 12px;
  width: 100%;
}

/* политика */
.zenemailcollectorV2-policy-link {
  color: var(--text);
  display: inline-block;
  line-height: 11px;
  text-decoration: none;
  border-bottom: 1px solid var(--text);
}

/* link базовый (как у них) */
.link {
  color: var(--link);
  text-decoration: none;
  transition: color 0.16s;
}

/* внутри EmailCollector они уменьшают текст чекбокса до 12px */
:deep(.zencheckbox-text) {
  font-size: 12px;
  color: var(--bench-text, #2d3137);
  line-height: 18px !important;
}

/* простая адаптация */
@media (max-width: 860px) {
  .zenemailcollectorV2-inner {
    flex-direction: column;
  }
  .zenemailcollectorV2-image {
    min-width: 100%;
    min-height: 220px;
  }
  .zenemailcollectorV2-button {
    margin-left: 0;
    margin-top: 12px;
  }
  .zenemailcollectorV2-submit {
    flex: 1 0 100%;
  }
}
</style>
