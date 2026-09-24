<template>
  <div v-if="configLoaded" class="bench-market purchase-page">
    <div class="simple-header">
      <div class="simple-header-content">
        <div class="header-logo" @click="goToMainPage">
          <img :src="logoSrc" alt="МАРКЕТ" />
        </div>
      </div>
    </div>

    <div class="purchase">
      <!-- <div class="topbar">
        <div class="title">Оформление заказа</div>
      </div> -->

      <div class="content mt-10">
        <div class="left">
          <div class="panel">
            <div class="panel-title">Заказ успешно оформлен</div>
          </div>
        </div>
        <div class="right"></div>
      </div>
    </div>
  </div>
  <div v-else />
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { syncMockLoggedInFromTrack } from '@/utils/localCache.js';
import { shopAssets } from '@/assets/shop-assets.js';

export default defineComponent({
  name: 'ShopPaymentSuccess',
  data() {
    return { loggedIn: false };
  },
  computed: {
    ...mapGetters(['trackConfig', 'kvStore']),
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    logoSrc() {
      const img = this.common && this.common.header && this.common.header.logo && this.common.header.logo.image;
      return img ? shopAssets[img] : shopAssets['logo'];
    } },
  methods: {
    goToMainPage() {
      this.$router.push({ name: 'bench_catalog_main', params: { state_id: 'state_main', track_id: this.$route.params.track_id } });
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

<style src="@/assets/shop.css"></style>

<style scoped>
.purchase-page { background-color: var(--bench-surface, #f2f3f5); min-height: 100vh; display: flex; flex-direction: column; }
.simple-header { background-color: var(--bench-surface, #f2f3f5); border-bottom: 1px solid #e6eaed; padding: 20px 0; }
.simple-header-content { max-width: 1400px; margin: 0 auto; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
.header-logo { flex-shrink: 0; }
.header-logo img { height: 44px; display: block; cursor: pointer; }
.purchase { max-width: 1200px !important; margin: 0 auto; padding: 0 16px; flex: 1; }
.topbar { padding: 16px 0; display: flex; flex-direction: column; align-items: flex-start; }
.topbar .title { font-size: 32px; font-weight: 700; line-height: 1.0; margin-top: -10px; }
.content { display: grid !important; grid-template-columns: 650px 1fr !important; gap: 24px !important; }
.panel { background: var(--bench-surface-elevated, #fff); border-radius: 25px !important; padding: 24px !important; margin-bottom: 12px; }
.panel-title { font-size: 24px; font-weight: 800; color: #001a34; }
@media (max-width: 1024px) {
  .content { grid-template-columns: 1fr !important; }
}
</style>


