<template>
  <div class="bench-hub">
    <h1 class="bench-hub__title">{{ siteTitle }}</h1>
    <div class="bench-hub__grid">
      <div
        v-for="section in cards"
        :key="section.id"
        class="bench-hub__card"
        :data-section="section.id"
        role="button"
        tabindex="0"
        @click="openSection(section)"
        @keydown.enter="openSection(section)"
      >
        <div class="bench-hub__card-icon">{{ section.icon }}</div>
        <div class="bench-hub__card-title">{{ section.label }}</div>
        <div class="bench-hub__card-desc">{{ section.description }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { PATCH_TRACK_CONFIG } from '@/store/mutations.type';
import { GET_KV_STORE, GET_TRACK_CONFIG } from '@/store/actions.type';
import { getBenchSections, mergeDomainIntoConfig } from '@/common/benchTheme';
import { pushBenchRoute } from '@/common/benchNavigation';
import { _logActivity } from '@/common/trackHelper';

const ICONS = {
  shop: '🛒',
  books: '📚',
  grocery: '🥬',
  rail: '🚆',
  hotels: '🏨',
  files: '📁',
};

const DESCRIPTIONS = {
  shop: 'Каталог товаров, корзина, избранное',
  books: 'Текстовые и аудиокниги',
  grocery: 'Доставка продуктов',
  rail: 'Поиск и покупка билетов',
  hotels: 'Поиск отелей и номеров',
  files: 'Коллекции документов и скачивание файлов',
};

export default {
  name: 'BenchHub',
  mixins: [StateDelayMixin],
  computed: {
    ...mapGetters(['trackConfig']),
    siteTitle() {
      return this.trackConfig?.test_data?.site_title || 'WebPageBench';
    },
    cards() {
      return getBenchSections(this.trackConfig)
        .filter((s) => s.domain && s.hub_visible !== false)
        .map((s) => ({
          ...s,
          icon: s.icon || ICONS[s.domain] || '▸',
          description: s.description || DESCRIPTIONS[s.domain] || '',
        }));
    },
  },
  methods: {
    openSection(section) {
      const trackId = this.$route.params.track_id;
      let config = this.trackConfig;
      if (section.domain) {
        config = mergeDomainIntoConfig(config, section.domain);
        this.$store.commit(PATCH_TRACK_CONFIG, config);
        const kvPath = config?.test_data?.kv_store_path;
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath });
        }
      }
      _logActivity(this, {
        type: 'state_changed',
        new_state: section.view_type,
        state_id: section.state,
        new_path: section.view_type,
      });
      pushBenchRoute(this.$router, {
        name: section.view_type,
        stateId: section.state,
        trackId,
      });
    },
  },
  mounted() {
    const trackId = this.$route.params.track_id;
    if (trackId && (!this.trackConfig || !Object.keys(this.trackConfig).length)) {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId });
    }
    this.applyStateDelay?.();
  },
};
</script>

<style src="@/assets/bench.css"></style>
