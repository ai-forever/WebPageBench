<template>
  <div class="bench-files">
    <section class="bench-files__heading">
      <p class="bench-files__eyebrow">Файлы</p>
      <h1 class="bench-files__title">Коллекции</h1>
    </section>
    <section
      class="bench-files__layout"
      :class="'bench-files__layout--' + collectionsVariant"
    >
      <nav class="bench-files__nav collection-nav" aria-label="Коллекции">
        <button
          v-for="collection in collections"
          :key="collection.id"
          type="button"
          class="bench-files__nav-btn"
          :class="{ 'bench-files__nav-btn--active': collection.id === selectedId }"
          @click="chooseCollection(collection)"
        >
          {{ collection.label }}
        </button>
      </nav>
    </section>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { GET_TRACK_CONFIG } from '@/store/actions.type';
import { mergeDomainIntoConfig } from '@/common/benchTheme';
import { PATCH_TRACK_CONFIG } from '@/store/mutations.type';
import { pushBenchRoute } from '@/common/benchNavigation';
import { _logActivity } from '@/common/trackHelper';
import {
  getFilesCollections,
  getFilesUiVariant,
  rememberCollection,
} from './filesHelpers.js';

export default {
  name: 'BenchFilesCabinet',
  mixins: [StateDelayMixin],
  computed: {
    ...mapGetters(['trackConfig']),
    collections() {
      return getFilesCollections(this.trackConfig);
    },
    collectionsVariant() {
      return getFilesUiVariant(this.trackConfig, 'collections', 'cards');
    },
    selectedId() {
      return this.$route.query.collection || '';
    },
  },
  methods: {
    ensureDomain() {
      const merged = mergeDomainIntoConfig(this.trackConfig, 'files');
      this.$store.commit(PATCH_TRACK_CONFIG, merged);
    },
    chooseCollection(collection) {
      if (!collection || !collection.id) return;
      rememberCollection(collection.id);
      _logActivity(this, {
        type: 'bench_files_select_collection',
        collection: collection.id,
      });
      const trackId = this.$route.params.track_id;
      pushBenchRoute(this.$router, {
        name: 'bench_files_collection',
        stateId: 'state_files_collection',
        trackId,
        query: { collection: collection.id },
      });
    },
  },
  mounted() {
    const trackId = this.$route.params.track_id;
    if (trackId && (!this.trackConfig || !Object.keys(this.trackConfig).length)) {
      this.$store.dispatch(GET_TRACK_CONFIG, { trackId }).then(() => this.ensureDomain());
    } else {
      this.ensureDomain();
    }
    this.applyStateDelay?.();
  },
};
</script>

<style src="@/assets/bench.css"></style>
