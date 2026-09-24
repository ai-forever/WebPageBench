<template>
  <nav v-if="visible" class="bench-top-nav" aria-label="Навигация бенчмарка">
    <div class="bench-top-nav__inner">
      <span class="bench-top-nav__brand">{{ siteTitle }}</span>
      <button
        v-for="section in sections"
        :key="section.id"
        type="button"
        class="bench-top-nav__link"
        :class="{ 'bench-top-nav__link--active': section.id === activeId }"
        @click="goSection(section)"
      >
        {{ section.label }}
      </button>
    </div>
  </nav>
</template>

<script>
import { mapGetters } from 'vuex';
import { PATCH_TRACK_CONFIG } from '@/store/mutations.type';
import { GET_KV_STORE } from '@/store/actions.type';
import {
  getBenchSections,
  isUnifiedBench,
  mergeDomainIntoConfig,
} from '@/common/benchTheme';

export default {
  name: 'BenchTopNav',
  computed: {
    ...mapGetters(['trackConfig']),
    visible() {
      return isUnifiedBench(this.trackConfig);
    },
    siteTitle() {
      return this.trackConfig?.test_data?.site_title || 'WebPageBench';
    },
    sections() {
      return getBenchSections(this.trackConfig);
    },
    activeId() {
      const name = this.$route?.name || '';
      const match = this.sections.find((s) => s.view_type === name);
      if (match) return match.id;
      if (name === 'bench_main') return 'hub';
      if (name === 'bench_catalog_basket') return 'shop';
      if (name === 'bench_books_basket') return 'books';
      if (name === 'bench_grocery_basket') return 'grocery';
      if (name && name.startsWith('bench_hotel_')) return 'hotels';
      if (name && name.startsWith('bench_rail_')) return 'rail';
      if (name && name.startsWith('bench_files_')) return 'files';
      const domain = this.trackConfig?.test_data?.active_bench_domain;
      if (domain === 'shop') return 'shop';
      if (domain === 'books') return 'books';
      if (domain === 'grocery') return 'grocery';
      return domain || '';
    },
  },
  methods: {
    goSection(section) {
      const trackId = this.$route.params.track_id;
      if (!trackId || !section.state || !section.view_type) return;

      let config = this.trackConfig;
      if (section.domain) {
        config = mergeDomainIntoConfig(config, section.domain);
        this.$store.commit(PATCH_TRACK_CONFIG, config);
        const kvPath = config?.test_data?.kv_store_path;
        if (kvPath) {
          this.$store.dispatch(GET_KV_STORE, { kvPath });
        }
      }

      this.$router.push({
        name: section.view_type,
        params: { track_id: trackId, state_id: section.state },
      });
    },
  },
};
</script>
