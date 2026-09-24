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
    <div v-if="!isLoggedIn" class="my-books-placeholder">
      <div class="title">Мои книги</div>
      <div class="subtitle">Читаю и слушаю</div>
      <div class="hint">Здесь будет появляться все, что вы читаете и слушаете</div>
      <div class="actions">
        <v-btn class="login" variant="flat" @click="openLoginDialog">Войти</v-btn>
      </div>
    </div>

    <div v-else class="my-books-main">
      <div class="title">Мои книги</div>
      <div v-if="purchasedKeys.length === 0" class="stub">Нет купленных книг</div>
      <div v-else class="items">
        <div v-if="isLoading" class="items-loader" style="display:flex;align-items:center;justify-content:center;min-height:200px;">
          <v-progress-circular indeterminate color="primary" :size="48"></v-progress-circular>
        </div>
        <template v-else>
          <div class="p-item" v-for="pi in purchasedResolvedItems" :key="pi.key">
            <div class="thumb">
              <book-cover :item="pi.item" />
            </div>
            <div class="info">
              <div class="book-name">{{ (pi.item && (pi.item.name || pi.item.title)) || pi.key }}</div>
              <div v-if="pi.item && pi.item.author" class="author">{{ pi.item.author }}</div>
            </div>
            <div class="actions">
              <v-btn variant="text" color="#ef4444" @click="removePurchased(pi.key)">
                <v-icon size="18">mdi-trash-can-outline</v-icon>
                <span>Удалить</span>
              </v-btn>
            </div>
          </div>
        </template>
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

</template>

<script>
import { defineComponent } from "vue";
import { mapGetters } from "vuex";
import SearchBar from "../../ui/SearchBar.vue";
import MenuBar from "../../ui/MenuBar.vue";
import ShopItemCarousel from "../../ui/ShopItemCarousel.vue";
import LoginDialog from "../../ui/LoginDialog.vue";
import BookCover from "./BookCover.vue";
import { isLoggedIn, setCurrentUsername, getPurchasedItems, removePurchasedItem } from "@/utils/localCache.js";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { StateDelayMixin } from "@/common/stateDelayMixin.js";

export default defineComponent({
  name: "BooksMyBooks",
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar, ShopItemCarousel, LoginDialog, BookCover },
  data() {
    return { isLoading: false, loginDialog: false, loggedIn: false, purchasedKeys: [] };
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      setCurrentUsername(username);
      this.loginDialog = false;
      this.refreshPurchased();
    },
    getTrackConfig() {
      this.isLoading = true;
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return Promise.resolve();
          }
          const kvPath = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.kv_store_path) || "";
          let kvPromise = Promise.resolve();
          if (kvPath) {
            kvPromise = this.$store.dispatch(GET_KV_STORE, { kvPath });
          }
          if (!this.trackConfig[this.$route.params.state_id]) {
            this.$router.push({ name: "state_not_found" });
          }          
          this.loggedIn = isLoggedIn();
          this.refreshPurchased();
          this.applyStateDelay();
          return kvPromise;
        })
        .finally(() => {
          this.isLoading = false;
        });
    },
    refreshPurchased() {
      if (!this.loggedIn) {
        this.purchasedKeys = [];
        return;
      }
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      this.purchasedKeys = getPurchasedItems(username);
    },
    removePurchased(key) {
      const username = (this.testData && this.testData.login_data && this.testData.login_data.login) || 'guest';
      removePurchasedItem(username, key);
      this.refreshPurchased();
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
    },
    purchasedResolvedItems() {
      const kv = this.kvStore || {};
      return (this.purchasedKeys || []).map(k => ({ key: k, item: kv[k] || null }));
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
    } },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
    this.loggedIn = isLoggedIn();
    this.refreshPurchased();
  } });
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.bench-books { --shop-max-width: 1600px; }
</style>


