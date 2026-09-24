<template>
  <div v-if="configLoaded" class="bench-grocery">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
    />
    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>

    <div v-if="contentReady" class="profile-section">
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
</div>
  <div v-else />
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from '../../ui/MenuBar.vue';
import BenchProfileInfoCard from '../../ui/BenchProfileInfoCard.vue';
import { getBenchPersonalInfo } from '@/common/benchPersonalInfo.js';
import { applyDefaultMockLoginFromTrackConfig, isGroceryLoggedIn, clearGroceryLogin } from '@/utils/localCache.js';
import { GET_TRACK_CONFIG } from '@/store/actions.type';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { pushBenchRoute } from '@/common/benchNavigation';

export default defineComponent({
  name: 'GroceryProfile',
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, BenchProfileInfoCard },
  data() {
    return { loggedIn: false };
  },
  computed: {
    ...mapGetters(['trackConfig']),
    isLoggedIn() { return this.loggedIn; },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    personalInfo() {
      return getBenchPersonalInfo(this.trackConfig);
    } },
  methods: {
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: 'not_found' });
            return;
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: 'state_not_found' });
          }
    this.loggedIn = isGroceryLoggedIn();
          this.applyStateDelay();
        });
    },
    logout() {
      clearGroceryLogin();
      this.loggedIn = false;
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_main',
        stateId: 'state_main',
        trackId: this.$route.params.track_id });
    } },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    applyDefaultMockLoginFromTrackConfig(this.trackConfig);
    this.loggedIn = isGroceryLoggedIn();
    if (!this.loggedIn) {
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_authorization',
        stateId: 'state_authorization',
        trackId: this.$route.params.track_id });
    }
  } });
</script>

<style scoped>
.bench-grocery {
  --shop-max-width: 1600px;
  height: auto;
  min-height: 100%;
  overflow: visible;
  display: block;
  background: var(--bench-surface, #f0f3f7);
}

.loading-container {
  display: flex;
  justify-content: center;
  padding: 48px 0;
}
</style>

<style src="@/assets/books.css"></style>
