<template>
  <div v-if="pagesDemo" class="pages-home">
    <p class="brand">WebPageBench</p>
    <h1>Маркет</h1>
    <p class="lead">
      Тот же интерфейс, что в бенче: поиск, карточка товара и корзина.
      Две темы одного задания. Остальные разделы сюда не входят.
    </p>
    <blockquote>
      В «Маркете» найдите сухой корм Purina ONE для стерилизованных кошек
      с говядиной и пшеницей и добавьте в корзину.
    </blockquote>
    <div class="choices">
      <router-link class="choice" :to="lightTo">
        <span class="kicker">Светлая тема</span>
        <strong>ecommerce_basket_named_product_02</strong>
        <span class="go">Открыть Маркет</span>
      </router-link>
      <router-link class="choice choice-dark" :to="darkTo">
        <span class="kicker">Тёмная тема</span>
        <strong>ecommerce_basket_named_product_02__theme_dark</strong>
        <span class="go">Открыть Маркет</span>
      </router-link>
    </div>
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

const shopRoute = (trackId) => ({
  name: "bench_catalog_main",
  params: { track_id: trackId, state_id: "state_shop_main" },
});

export default defineComponent({
  name: "HomeView",
  data() {
    return {
      API_URL,
      trackId: "",
      pagesDemo: import.meta.env.VITE_PAGES_DEMO === "1",
      lightTo: shopRoute("demo-light"),
      darkTo: shopRoute("demo-dark"),
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
  max-width: 880px;
  margin: 0 auto;
  padding: 48px 20px 72px;
  color: #2c3e50;
}
.brand {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #4a6fa5;
}
h1 {
  margin: 0 0 12px;
  font-size: 40px;
  line-height: 1.1;
}
.lead {
  margin: 0 0 20px;
  font-size: 18px;
  max-width: 62ch;
}
blockquote {
  margin: 0 0 24px;
  padding: 14px 16px;
  background: #fff;
  border-left: 4px solid #4a6fa5;
  border-radius: 0 12px 12px 0;
}
.choices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.choice {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px;
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
.choice strong { font-size: 15px; overflow-wrap: anywhere; }
.go { margin-top: 8px; font-weight: 700; }
@media (max-width: 720px) {
  .choices { grid-template-columns: 1fr; }
  h1 { font-size: 32px; }
}
</style>
