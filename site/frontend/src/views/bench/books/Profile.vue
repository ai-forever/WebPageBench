<template>
  <div v-if="configLoaded" class="bench-books">    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady">
    <!-- MAIN SECTION -->

    <div class="profile-section">
      <div class="container">
        <div class="profile-card">
          <div class="left">
            <v-avatar size="72" class="avatar" rounded>
              <v-icon size="48">mdi-account-circle</v-icon>
            </v-avatar>
            <div class="user-info">
              <bench-profile-info-card :info="personalInfo" variant="books" show-greeting />
            </div>
          </div>
          <div class="right">
            <v-btn class="logout" variant="text" @click="logout">Выход</v-btn>
          </div>
        </div>
      </div>
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
import BenchProfileInfoCard from "../../ui/BenchProfileInfoCard.vue";
import { getBenchPersonalInfo } from "@/common/benchPersonalInfo.js";
import { isLoggedIn, setLoggedIn } from "@/utils/localCache.js";

import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksProfile",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, ShopItemCarousel, LoginDialog, BenchProfileInfoCard },
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
    logout() {
      setLoggedIn(false);
      this.loggedIn = false;
      this.$router.push({ name: 'bench_books_main', params: { state_id: 'state_main', track_id: this.$route.params.track_id } });
    }
  },
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
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    },
    userFullName() {
      return this.personalInfo.fullName;
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
    if (!this.loggedIn) {
      this.$router.push({ name: 'bench_books_main', params: { state_id: 'state_main', track_id: this.$route.params.track_id } });
    }
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }
</style>