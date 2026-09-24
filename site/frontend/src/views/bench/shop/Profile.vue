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

    <!-- Logged out CTA -->
    <div v-if="!isLoggedIn" class="guest-cta">
      <div class="guest-cta-box">
        <div class="guest-cta-title">Войдите или зарегистрируйтесь</div>
        <div class="guest-cta-text">Чтобы делать покупки, отслеживать заказы и пользоваться персональными скидками и баллами.</div>
        <v-btn color="#0b63ff" variant="flat" class="guest-cta-btn" @click="openLoginDialog">Войти или зарегистрироваться</v-btn>
      </div>
      <!-- Simple secondary blocks -->
      <div class="guest-cta-secondary">
        <div class="guest-cta-secondary-title">Стоимость доставки и пункты выдачи</div>
        <div class="guest-cta-secondary-text">Укажите свой населенный пункт, чтобы увидеть пункты выдачи</div>
        <div class="guest-cta-secondary-actions">
          <v-btn variant="tonal">Перейти к карте</v-btn>
          <v-btn variant="tonal">Узнать о стоимости доставки</v-btn>
        </div>
      </div>
    </div>

    <!-- Logged in profile -->
    <div v-else class="profile">
      <div class="sidebar">
        <div v-for="(grp, i) in (content && content.sidebar) || []" :key="'g'+i" class="group">
          <div class="title">{{ grp.title }}</div>
          <div class="item" v-for="(it, j) in grp.items" :key="'i'+j">{{ it.caption }}</div>
        </div>
      </div>
      <div class="main">
        <div class="hello">Профиль</div>
        <div class="user-info-card">
          <bench-profile-info-card :info="personalInfo" />
        </div>
        <div class="actions"><v-btn class="logout" variant="text" @click="logout">Выход</v-btn></div>
        <div class="tiles">
          <div v-for="(t, k) in content.tiles || []" :key="'t'+k" class="tile">
            <div class="t-title">{{ t.title }}</div>
            <div class="t-value">{{ t.value }}</div>
          </div>
        </div>
      </div>
    </div>

    <shop-login-dialog v-model="loginDialog" :loginData="testData && testData.login_data" @success="onLoginSuccess" />
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { benchUserContextMixin } from '@/common/benchUserContextMixin.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from './components/MenuBar.vue';
import { GET_TRACK_CONFIG } from '@/store/actions.type';
import { syncMockLoggedInFromTrack, setLoggedIn, setCurrentUsername } from '@/utils/localCache.js';
import ShopLoginDialog from './components/ShopLoginDialog.vue';
import BenchProfileInfoCard from '@/views/ui/BenchProfileInfoCard.vue';

export default defineComponent({
  name: 'ShopProfile',
  mixins: [benchUserContextMixin],
  components: { SearchBar, ShopLoginDialog, MenuBar, BenchProfileInfoCard },
  data() { return { loginDialog: false, loggedIn: false }; },
  computed: {
    ...mapGetters(['trackConfig']),
    configLoaded() { return this.trackConfig && Object.keys(this.trackConfig).length > 0; },
    common() { return (this.trackConfig && this.trackConfig.common_elements) || {}; },
    content() { const st = this.trackConfig[this.$route.params.state_id]; return st && st.content || {}; },
    testData() { return (this.trackConfig && this.trackConfig.test_data) || {}; },
    userFullName() { return this.personalInfo.fullName; },
    isLoggedIn() { return this.loggedIn; }
  },
  methods: {
    openLoginDialog() { this.loginDialog = true; },
    onLoginSuccess() {
      this.loggedIn = true;
      const username = this.benchSessionUser || 'guest';
      setCurrentUsername(username);
    },
    logout() {
      setLoggedIn(false);
      this.$router.push({ name: 'bench_catalog_main', params: { state_id: 'state_main', track_id: this.$route.params.track_id } });
    }
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id }).then(() => { this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig); });
    } else {
      this.loggedIn = syncMockLoggedInFromTrack(this.trackConfig);
    }
  }
});
</script>

<style src="@/assets/books.css"></style>
<style src="@/assets/shop.css"></style>

