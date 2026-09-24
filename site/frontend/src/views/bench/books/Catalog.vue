<template>
  <div v-if="configLoaded" class="bench-books">    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady">
    <!-- MAIN SECTION -->

    <div class="catalog-placeholder">
      <div class="title">Каталог</div>
      <div class="subtitle">Список книг</div>
    </div>
    <!-- END MAIN SECTION -->

    <shop-item-carousel
      v-if="common && common.item_carousel"
      :title="common.item_carousel.title"
      :items="carouselItems"
    />
</div>
  </div>
  <div v-else />
  
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import ShopItemCarousel from "../../ui/ShopItemCarousel.vue";
import LoginDialog from "../../ui/LoginDialog.vue";

import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { isLoggedIn } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksCatalog",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, ShopItemCarousel, LoginDialog },
  data() {
    return { isLoading: false, loginDialog: false, loggedIn: false };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          if (kvPath) {
            this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: "state_not_found" });
          }
          this.loggedIn = isLoggedIn();
          this.applyStateDelay();
        });
    },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.loginDialog = false;
    } },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() { return this.loggedIn; },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    content() {
      return this.trackConfig[this.$route.params.state_id].content;
    },
    carouselItems() {
      const src = (this.common && this.common.item_carousel && this.common.item_carousel.items) || [];
      const kv = this.kvStore || {};
      return src.map(it => {
        if (it && it.kv_id && kv[it.kv_id]) {
          const kvItem = kv[it.kv_id];
          return { ...kvItem, ...it };
        }
        return it;
      });
    } },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }

/* Catalog placeholder styles */
.bench-books .catalog-placeholder { padding: 24px 16px 40px; max-width: var(--shop-max-width); margin: 0 auto; }
.bench-books .catalog-placeholder .title { font-size: 28px; font-weight: 800; color: #15223b; margin: 0 0 16px 0; }
.bench-books .catalog-placeholder .subtitle { font-size: 18px; font-weight: 300; color: #15223b; }
</style>


