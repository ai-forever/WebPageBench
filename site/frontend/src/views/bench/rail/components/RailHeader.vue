<template>
  <header class="rail-header">
    <div class="header-inner">
      <router-link :to="mainTo" class="logo-link">
        <img :src="railLogo" alt="" class="logo-img" />
      </router-link>
      <nav class="main-nav">
        <a href="#" class="active">Пассажирам</a>
        <a href="#">Грузовые перевозки</a>
        <a href="#">Компания</a>
        <a href="#">Вакансии</a>
        <a href="#">Контакты</a>
      </nav>
      <div class="header-right">
        <a href="#"><span style="font-size: 12px; padding-right: 2px;">Версия для слабовидящих</span><v-icon size="25">mdi-eye-outline</v-icon></a>
        <a v-if="!isLoggedIn" href="#" @click.prevent="handleLoginClick" style="border-left: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0; padding: 0 15px;"><span style="font-size: 12px; padding-right: 2px;">Вход</span><v-icon size="25">mdi-login</v-icon></a>
        <span v-else class="user-area" style="border-left: 1px solid #e0e0e0; border-right: 1px solid #e0e0e0; padding: 0 15px; display: inline-flex; align-items: center;">
          <router-link :to="profileTo" style="font-size: 12px; padding-right: 8px; color: inherit; text-decoration: none;">{{ userName }}</router-link>
          <a href="#" @click.prevent="handleLogoutClick" style="display: inline-flex; align-items: center;"><span style="font-size: 12px; padding-right: 2px;">Выход</span><v-icon size="25">mdi-logout</v-icon></a>
        </span>
        <a href="#"><span style="font-size: 12px; padding-right: 2px;">Rus</span><v-icon size="14">mdi-chevron-down</v-icon></a>
        <a href="#"><v-icon size="38">mdi-magnify</v-icon></a>
      </div>
    </div>
  </header>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailHeader",
  props: {
    railLogo: {
      type: String,
      required: true,
    },
    isLoggedIn: {
      type: Boolean,
      default: false,
    },
    userName: {
      type: String,
      default: "",
    },
  },
  emits: ["open-login", "logout"],
  computed: {
    mainTo() {
      const { track_id, state_id } = (this.$route && this.$route.params) || {};
      if (track_id && state_id) {
        return { name: "bench_rail_main", params: { track_id, state_id } };
      }
      return { name: "main" };
    },
    profileTo() {
      const { track_id } = (this.$route && this.$route.params) || {};
      if (track_id) {
        return { name: "bench_rail_profile", params: { track_id, state_id: "state_profile" } };
      }
      return { name: "main" };
    },
  },
  methods: {
    handleLoginClick() {
      this.$emit("open-login");
    },
    handleLogoutClick() {
      this.$emit("logout");
    },
  },
});
</script>

<style src="@/assets/rail.css"></style>
