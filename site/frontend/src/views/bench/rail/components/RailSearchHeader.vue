<template>
  <header class="rail-header rail-search-header">
    <div class="header-inner">
      <router-link :to="logoTo" class="logo-link" aria-label="На главную">
        <img :src="railLogo" alt="" class="logo-img" />
      </router-link>
      <div class="header-right">
        <a href="#" class="header-icon-link"><v-icon size="22">mdi-share-variant-outline</v-icon></a>
        <a href="#" class="header-icon-link"><v-icon size="22">mdi-link-variant</v-icon></a>
        <a v-if="!isLoggedIn" href="#" class="header-link login-link" @click.prevent="handleLoginClick">
          <v-icon size="22">mdi-login</v-icon>
          <span>Войти</span>
        </a>
        <a v-else href="#" class="header-icon-link user-icon" @click.prevent="handleLoginClick">
          <v-icon size="24">mdi-account-outline</v-icon>
        </a>
        <a href="#" class="header-link lang-link"><span>RU</span></a>
        <button class="menu-btn" @click.prevent="handleLoginClick">
          <v-icon size="24">mdi-menu</v-icon>
        </button>
      </div>
    </div>
  </header>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailSearchHeader",
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
    logoTo() {
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

<style scoped>
.bench-rail .logo-img {
  width: 70px;
}

.rail-search-header .header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rail-search-header .header-icon-link {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 40px;
  color: #333;
  text-decoration: none;
  border-right: 1px solid #e0e0e0;
}

.rail-search-header .header-icon-link:hover {
  color: #e21a1a;
}

.rail-search-header .header-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 22px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}

.rail-search-header .header-link:hover {
  color: #e21a1a;
}

.rail-search-header .login-link {
  border-right: 1px solid #e0e0e0;
}

.rail-search-header .user-icon {
  padding-right: 16px;
}

.rail-search-header .menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  cursor: pointer;
  color: #333;
}

.rail-search-header .menu-btn:hover {
  color: #e21a1a;
}
</style>