<template>
  <div v-if="configLoaded" class="bench-grocery">
    <search-bar
      :logo="common.search_bar && common.search_bar.logo"
      :search-placeholder="common.search_bar && common.search_bar.searchPlaceholder"
      :search-button-caption="common.search_bar && common.search_bar.searchButtonCaption"
      :panel-buttons="common.search_bar && common.search_bar.panelButtons"
      :logged-in="isUserLoggedIn"
    />
    <menu-bar :items="(common.menu_bar && common.menu_bar.items) || []" />

    <div class="catalog-page">
      <h1 class="section-title">Каталог</h1>
      <p class="catalog-subtitle">Категории продуктов</p>
      <div class="catalog-groups">
        <div v-for="(group, gIdx) in catalogGroups" :key="'g' + gIdx" class="catalog-group">
          <h2 v-if="group.title" class="group-title">{{ group.title }}</h2>
          <div class="catalog-links">
            <button
              v-for="(item, iIdx) in group.items"
              :key="'c' + gIdx + '-' + iIdx"
              class="catalog-link"
              type="button"
              @click="openCategory(item.id)"
            >
              {{ item.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import { GET_TRACK_CONFIG } from '@/store/actions.type';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { pushBenchRoute } from '@/common/benchNavigation';
import { applyDefaultMockLoginFromTrackConfig, isGroceryLoggedIn } from '@/utils/localCache.js';
import SearchBar from '../../ui/SearchBar.vue';
import MenuBar from '../../ui/MenuBar.vue';

export default defineComponent({
  name: 'GroceryCatalog',
  mixins: [StateDelayMixin],
  components: { SearchBar, MenuBar },
  data() {
    return { isUserLoggedIn: false };
  },
  computed: {
    ...mapGetters(['trackConfig']),
    configLoaded() {
      return this.trackConfig && Object.keys(this.trackConfig).length > 0;
    },
    common() {
      return (this.trackConfig && this.trackConfig.common_elements) || {};
    },
    catalogGroups() {
      const groups = [];
      const leftItems = (this.common.leftMenu && this.common.leftMenu.items) || [];
      leftItems.forEach((block) => {
        const cats = Array.isArray(block.categories) ? block.categories : [];
        const items = cats
          .filter((c) => c && c.id)
          .map((c) => ({ name: c.name || c.id, id: c.id }));
        if (items.length) {
          groups.push({ title: block.caption || '', items });
        }
      });
      return groups;
    },
  },
  methods: {
    openCategory(categoryId) {
      if (!categoryId) return;
      pushBenchRoute(this.$router, {
        name: 'bench_grocery_category',
        stateId: String(categoryId),
        trackId: this.$route.params.track_id,
      });
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          applyDefaultMockLoginFromTrackConfig(this.trackConfig);
          this.isUserLoggedIn = isGroceryLoggedIn();
          this.applyStateDelay();
        });
    },
  },
  mounted() {
    applyDefaultMockLoginFromTrackConfig(this.trackConfig);
    this.isUserLoggedIn = isGroceryLoggedIn();
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    } else {
      this.applyStateDelay();
    }
  },
});
</script>

<style src="@/assets/books.css"></style>
<style scoped>
.catalog-page {
  max-width: var(--shop-max-width, 1600px);
  margin: 0 auto;
  padding: 24px 16px 40px;
}
.section-title {
  font-size: 28px;
  font-weight: 800;
  color: #15223b;
  margin: 0 0 8px;
}
.catalog-subtitle {
  font-size: 18px;
  font-weight: 300;
  color: #15223b;
  margin: 0 0 24px;
}
.catalog-group {
  margin-bottom: 28px;
}
.group-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #15223b;
}
.catalog-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.catalog-link {
  border: 1px solid #d7dde3;
  background: #fff;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  cursor: pointer;
  color: #15223b;
}
.catalog-link:hover {
  background: #f3f5f7;
}
</style>
