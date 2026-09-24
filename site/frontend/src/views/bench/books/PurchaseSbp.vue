<template>
  <div v-if="configLoaded" class="bench-books">

    <!-- MAIN SECTION -->
    <div class="purchase-main">
      <div class="title">Оформление покупки</div>
      <div class="placeholder">Оплата по СБП</div>
    </div>
    <!-- END MAIN SECTION -->

  </div>
</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";

import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { isLoggedIn, setCurrentUsername } from "@/utils/localCache.js";

export default defineComponent({
  name: "BooksPurchaseSbp",
  components: { },
  data() {
    return { loginDialog: false, loggedIn: false };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
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
        });
    },
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
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    }
    this.loggedIn = isLoggedIn();
  },
});
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.purchase-main { max-width: var(--shop-max-width); margin: 24px auto; padding: 0 16px; }
.purchase-main .title { font-size: 28px; font-weight: 800; color: #15223b; margin-bottom: 16px; }
.purchase-main .placeholder { color: #6b7280; }
</style>


