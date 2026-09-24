<template>
  <div class="widgets">
    <!-- Favorites -->
    <div class="icon-base">
      <div class="icon-box"><FavoriteIcon /></div>
    </div>

    <!-- Notifications -->
    <div class="icon-base">
      <div class="icon-box"><BellIcon /></div>
    </div>

    <!-- Language (desktop up) -->
    <div class="icon-base">
      <div class="icon-box"><FlagIcon /></div>
    </div>

    <!-- Currency (desktop up) -->
    <div class="icon-base">
      <div class="icon-box"><CurrencyIcon /></div>
    </div>

    <!-- Support -->
    <div class="icon-base">
      <div class="icon-box"><SupportIcon /></div>
    </div>

    <!-- Sign in / account -->
    <div class="icon_text">
      <div class="icon-box"><UserIcon /></div>
      <div class="control-text">{{ userLabel }}</div>
    </div>

    <!-- Menu -->
    <div class="clickOutside">
      <div style="display: block;">
        <div class="menu_wrapper">
          <div class="menu_inner">
            <div class="menu">
              <BurgerIcon />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useStore } from "vuex";

import FavoriteIcon from "../icons/FavoriteIcon.vue";
import BellIcon from "../icons/BellIcon.vue";
import FlagIcon from "../icons/FlagIcon.vue";
import CurrencyIcon from "../icons/CurrencyIcon.vue";
import SupportIcon from "../icons/SupportIcon.vue";
import UserIcon from "../icons/UserIcon.vue";
import BurgerIcon from "../icons/BurgerIcon.vue";
import { getBenchPersonalInfo } from "@/common/benchPersonalInfo.js";

const store = useStore();
const trackConfig = computed(() => store.getters.trackConfig);
const isLoggedIn = computed(() => {
  const testData = trackConfig.value?.test_data || {};
  return testData.is_login !== false && Boolean(testData.login_data);
});
const userLabel = computed(() => {
  if (!isLoggedIn.value) return "Войти";
  return getBenchPersonalInfo(trackConfig.value).shortName || "Профиль";
});
</script>

<style scoped>
.menu {
  align-items: center;
  block-size: 40px;
  color: #0e41d2;
  display: flex;
  justify-content: center;
  position: relative;
}

.menu_inner {
  align-items: center;
  block-size: 48px;
  display: flex;
  justify-content: center;
  padding-inline-end: 20px;
  padding-inline-start: 10px;
  user-select: none;
}

.menu_wrapper {
  display: flex;
  inline-size: 100%;
}

.icon_text {
  /* background: none; */
  /* border: 0; */
  cursor: pointer;

  display: flex;
  inline-size: 100%;
  align-items: center;
}

.control-text {
  margin-inline-start: 8px;
  position: relative;
  white-space: nowrap;

  color: #0e41d2;
  font-size: 16px;
  font-weight: 480;
  line-height: 1.231;
  font-family: 'PTRootUI', Verdana, sans-serif;
}

.icon-box {
  align-items: center;
  aspect-ratio: 1 / 1;
  display: flex;
  justify-content: center;
  min-inline-size: 20px;
  position: relative;

  align-items: center;
  box-sizing: border-box;
  color: #0e41d2;
  display: flex;
  font-size: 16px;
  font-weight: 500;
  /* min-block-size: 34px; */
  position: relative;
  user-select: none;
}

.icon-base {
  cursor: pointer;
  padding: 2px 8px;
}

.widgets {
  align-items: center;
  display: flex;
  justify-content: flex-end;
  margin-inline-start: auto;
  column-gap: 4px;
}
</style>