<template>
  <div v-if="configLoaded" class="bench-books">    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isLoggedIn"
      @login="openLoginDialog"
    />
    <login-dialog
      v-model="loginDialog"
      :loginData="testData && testData.login_data"
      @success="onLoginSuccess"
    />
    <menu-bar :items="common.menu_bar && common.menu_bar.items" />
    <div v-if="!contentReady" class="loading-container">
      <v-progress-circular indeterminate color="primary" :size="64"></v-progress-circular>
    </div>
    <div v-if="contentReady">
    <!-- First carousel -->
    <shop-item-carousel
      v-if="kvStoreLoaded"
      :title="common.item_carousel && common.item_carousel.title"
      :items="carouselItems"
    />
    <div v-else-if="configLoaded" class="section">
      <div class="section-title">{{ common.item_carousel && common.item_carousel.title }}</div>
      <v-row class="skeleton-carousel">
        <v-col v-for="n in 6" :key="n" cols="2">
          <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
        </v-col>
      </v-row>
    </div>
    
    <!-- Second carousel -->
    <shop-item-carousel
      v-if="kvStoreLoaded"
      :title="common.item_carousel2 && common.item_carousel2.title"
      :items="carouselItems2"
    />
    <div v-else-if="configLoaded" class="section">
      <div class="section-title">{{ common.item_carousel2 && common.item_carousel2.title }}</div>
      <v-row class="skeleton-carousel">
        <v-col v-for="n in 6" :key="n" cols="2">
          <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
        </v-col>
      </v-row>
    </div>
    
    <!-- Third carousel -->
    <shop-item-carousel
      v-if="kvStoreLoaded"
      :title="common.item_carousel3 && common.item_carousel3.title"
      :items="carouselItems3"
    />
    <div v-else-if="configLoaded" class="section">
      <div class="section-title">{{ common.item_carousel3 && common.item_carousel3.title }}</div>
      <v-row class="skeleton-carousel">
        <v-col v-for="n in 6" :key="n" cols="2">
          <v-skeleton-loader type="image, article" elevation="0"></v-skeleton-loader>
        </v-col>
      </v-row>
    </div>
</div>
  </div>

</template>

<script>  
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG } from "@/store/actions.type";
import { GET_KV_STORE } from "@/store/actions.type";

import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import ShopItemCarousel from "../../ui/ShopItemCarousel.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import { isLoggedIn, getBasketItems, setCurrentUsername } from "@/utils/localCache.js";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

// import testConfig from "@/test/test_eshop_config.json";
// import testKvStore from "@/test/test_kv_eshop.json";

export default defineComponent({
  name: "BooksMain",
  mixins: [StateDelayMixin],
  components: {
        SearchBar,
    MenuBar,
        ShopItemCarousel, LoginDialog },
  data() {
    return {
      isLoading: false,
      loginDialog: false,
      loggedIn: false,
      kvStoreReady: false };
  },
  methods: {
    openLoginDialog() {
      this.loginDialog = true;
    },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.refreshBasket();
    },
    refreshBasket() {
      if (!this.loggedIn) {
        this.basketKeys = [];
        return;
      }
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      this.basketKeys = getBasketItems(username);
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
            this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
              this.kvStoreReady = true;
            });
          } else {
            // If no kvPath, mark kvStore as ready immediately
            this.kvStoreReady = true;
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: "state_not_found" });
          }
          this.loggedIn = isLoggedIn();
          this.applyStateDelay();
        });
    } },
  computed: {
    ...mapGetters(["trackConfig", "kvStore"]),
    isLoggedIn() {
      return this.loggedIn;
    },
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    kvStoreLoaded() {
      return this.kvStoreReady;
    },
    content() {
      return this.trackConfig[this.$route.params.state_id].content;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    testData() {
      return (this.trackConfig && this.trackConfig.test_data) || {};
    },
    // take item from kv store
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
    },
    carouselItems2() {
      const src = (this.common && this.common.item_carousel2 && this.common.item_carousel2.items) || [];
      const kv = this.kvStore || {};
      
      return src.map(it => {
        if (it && it.kv_id && kv[it.kv_id]) {
          const kvItem = kv[it.kv_id];
          return { ...kvItem, ...it };
        }
        return it;
      });
    },
    carouselItems3() {
      const src = (this.common && this.common.item_carousel3 && this.common.item_carousel3.items) || [];
      const kv = this.kvStore || {};
      
      return src.map(it => {
        if (it && it.kv_id && kv[it.kv_id]) {
          const kvItem = kv[it.kv_id];
          return { ...kvItem, ...it };
        }
        return it;
      });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
      console.log(this.trackConfig);
    } else {
      const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
      if (kvPath && !this.kvStoreReady) {
        this.$store.dispatch(GET_KV_STORE, { kvPath }).then(() => {
          this.kvStoreReady = true;
        });
      } else if (!kvPath) {
        this.kvStoreReady = true;
      }
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.skeleton-carousel {
  max-width: var(--shop-max-width);
  margin: 0 auto;
  padding: 0;
}

.skeleton-carousel .v-col {
  padding: 8px;
}

.skeleton-carousel :deep(.v-skeleton-loader__image) {
  height: 210px;
  border-radius: 12px;
}

.skeleton-carousel :deep(.v-skeleton-loader__article) {
  padding-top: 8px;
}

.skeleton-carousel :deep(.v-skeleton-loader) {
  background: transparent;
}
</style>