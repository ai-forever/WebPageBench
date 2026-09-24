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
    <div class="success-main">
      <div class="title">Мои книги</div>
      <div class="success-box">
        <div class="message">Поздравляем! Книга куплена</div>
        <v-btn class="go-btn" variant="flat" @click="goToMyBooks">Перейти к книге</v-btn>
      </div>
    </div>
    <!-- END MAIN SECTION -->
</div>
  </div>

</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import { isLoggedIn, setCurrentUsername } from "@/utils/localCache.js";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksPaymentSuccess",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, LoginDialog },
  data() {
    return { loginDialog: false, loggedIn: false };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.loginDialog = false;
    },
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
          this.loggedIn = isLoggedIn();
          this.applyStateDelay();
        });
    },
    goToMyBooks() {
      this.$router.push({ name: 'bench_books_my_books', params: { track_id: this.$route.params.track_id, state_id: 'state_my_books' } });
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
    content() {
      const state = this.$route && this.$route.params && this.$route.params.state_id;
      const cfg = state && this.trackConfig && this.trackConfig[state];
      return cfg ? cfg.content : {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
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
.success-main { max-width: var(--shop-max-width); margin: 24px auto; padding: 0 16px; }
.success-main .title { font-size: 28px; font-weight: 800; color: #15223b; margin-bottom: 16px; }
.success-box { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.success-box .message { font-weight: 700; color: #16a34a; }
.go-btn { background: #3b3bd8; color: #fff; text-transform: none; font-weight: 700; border-radius: 12px; }

</style>


