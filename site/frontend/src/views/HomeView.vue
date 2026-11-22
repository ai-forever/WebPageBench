<template>
  <div v-if="pagesDemo" class="pages-home">
    <header class="pages-home__bar">
      <span>WebPageBench</span>
    </header>
    <main class="pages-home__main">
      <h1>Главная</h1>
      <p class="lead">
        Те же разделы, что в бенче: Маркет, Книги, Продукты, Поезда, Отели и Файлы.
        Светлая и тёмная тема открываются отдельно. Внутри тему можно сменить кнопкой в шапке.
      </p>
      <div class="choices">
        <router-link class="choice" :to="lightTo">
          <span class="kicker">Светлая тема</span>
          <strong>Открыть главную</strong>
        </router-link>
        <router-link class="choice choice-dark" :to="darkTo">
          <span class="kicker">Тёмная тема</span>
          <strong>Открыть главную</strong>
        </router-link>
      </div>
      <p class="fine">
        Кнопка «События» в углу показывает действия на странице: переходы, клики и добавление в корзину.
      </p>
    </main>
  </div>
  <v-row v-else>
    <v-col cols="12" class="text-h5">Старт</v-col>
    <v-col>
      <div>Задание доступно по адресу <strong>host/&lt;track_id&gt;</strong></div>
      <v-card class="mt-5" elevation="2">
        <v-card-title>Инструменты</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <div>Просмотр логов событий: <strong>host/&lt;track_id&gt;/events</strong></div>
              <v-text-field v-model="trackId" label="Track ID" placeholder="Введите ID трека"></v-text-field>
              <v-btn color="primary" @click="goToEventLog">Перейти к логам событий</v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";

const hubRoute = (trackId) => ({
  name: "bench_hub",
  params: { track_id: trackId, state_id: "state_hub" },
});

export default defineComponent({
  name: "HomeView",
  data() {
    return {
      API_URL,
      trackId: "",
      pagesDemo: import.meta.env.VITE_PAGES_DEMO === "1",
      lightTo: hubRoute("demo-light"),
      darkTo: hubRoute("demo-dark"),
    };
  },
  methods: {
    goToEventLog() {
      if (this.trackId) {
        this.$router.push({ name: "event_log", params: { track_id: this.trackId } });
      }
    },
  },
});
</script>

<style scoped>
.pages-home {
  min-height: 100vh;
  background: #f0f3f7;
  color: #2c3e50;
}
.pages-home__bar {
  padding: 14px 24px;
  background: #3d5a80;
  color: #e8eef5;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.pages-home__main {
  max-width: 880px;
  margin: 0 auto;
  padding: 48px 20px 72px;
}
h1 {
  margin: 0 0 12px;
  font-size: 40px;
  line-height: 1.1;
}
.lead, .fine {
  margin: 0 0 24px;
  max-width: 62ch;
  font-size: 18px;
}
.fine { margin-top: 22px; font-size: 15px; color: #5c6e84; }
.choices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.choice {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 22px;
  text-decoration: none;
  color: #2c3e50;
  background: #fff;
  border: 1px solid #d5deea;
  border-radius: 16px;
}
.choice-dark {
  background: #232a3b;
  color: #e8eef5;
  border-color: #3d4a5c;
}
.kicker { font-size: 13px; font-weight: 700; color: #4a6fa5; }
.choice-dark .kicker { color: #9db7d8; }
.choice strong { font-size: 22px; }
@media (max-width: 720px) {
  .choices { grid-template-columns: 1fr; }
  h1 { font-size: 32px; }
}
</style>
