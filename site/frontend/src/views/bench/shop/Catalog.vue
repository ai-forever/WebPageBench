<template>
  <div v-if="configLoaded" class="bench-market">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <div class="menu-wrap menu-rounded pb-4">
      <menu-bar
        :items="(common.menu && common.menu.items) || []"
        :logged-in="isLoggedIn"
        :delivery-type="shopUser.delivery_type"
        :address="shopUser.address"
      />
    </div>

    <div class="grid catalog-placeholder">
      <div class="grid-title catalog-title">Каталог</div>
    </div>
    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
  <div v-else />
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import MenuBar from './components/MenuBar.vue';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import SearchBar from '../../ui/SearchBar.vue';
import BannerLine from '../../ui/BannerLine.vue';
import { shopAssets } from '@/assets/shop-assets.js';
import { syncMockLoggedInFromTrack, setCurrentUsername } from '@/utils/localCache.js';

export default defineComponent({
  name: 'ShopCatalog',
  mixins: [benchUserContextMixin],
  components: { MenuBar, ShopLoginDialog, SearchBar, BannerLine },
  data() { return { loginDialog: false, loggedIn: false }; },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    isLoggedIn() { return this.loggedIn; },
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    menuBgImage() {
      const img = this.common && this.common.menu && this.common.menu.background && this.common.menu.background.image;
      return img ? shopAssets[img] : '';
    }
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || '';
          if (kvPath) return this.$store.dispatch(GET_KV_STORE, { kvPath });
          return Promise.resolve();
        });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    }
    this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
  }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>


