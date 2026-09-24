<template>
  <div class="bench-files">
    <section class="bench-files__heading">
      <p class="bench-files__eyebrow">Файлы</p>
      <h1 class="bench-files__title">{{ selectedCollection ? selectedCollection.label : 'Коллекция' }}</h1>
    </section>

    <section v-if="selectedCollection" class="bench-files__content file-content">
      <label v-if="yearsVariant === 'select'" class="bench-files__field field">
        <span>Год</span>
        <select :value="selectedYear" @change="chooseYear($event.target.value)">
          <option value="" disabled>Выберите год</option>
          <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
        </select>
      </label>

      <fieldset v-else class="bench-files__years year-chips">
        <legend>Год</legend>
        <label v-for="year in years" :key="year" class="bench-files__year">
          <input
            :type="yearsVariant === 'radio' ? 'radio' : 'checkbox'"
            name="year"
            :value="year"
            :checked="selectedYear === year"
            @change="chooseYear(year)"
          />
          {{ year }}
        </label>
      </fieldset>

      <p v-if="!selectedYear" class="bench-files__empty">
        Выберите год, чтобы увидеть доступные файлы.
      </p>

      <article
        v-for="file in yearFiles"
        :key="file.file"
        class="bench-files__card file-card"
      >
        <span class="bench-files__symbol file-symbol">{{ formatLabel(file) }}</span>
        <div>
          <b>{{ file.file }}</b>
          <p>{{ fileAddedLabel(file, selectedYear) }}</p>
        </div>
        <a
          :class="downloadClass"
          :href="fileHref(file)"
          download
          aria-label="Скачать локальный файл"
          @click="download(file)"
        >{{ downloadLabel }}</a>
      </article>
    </section>

    <p v-else class="bench-files__empty">Выберите коллекцию в разделе «Файлы».</p>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { StateDelayMixin } from '@/common/stateDelayMixin.js';
import { GET_TRACK_CONFIG } from '@/store/actions.type';
import { mergeDomainIntoConfig } from '@/common/benchTheme';
import { PATCH_TRACK_CONFIG } from '@/store/mutations.type';
import { _logActivity } from '@/common/trackHelper';
import {
  fileAddedLabel,
  fileHref,
  getFilesCollections,
  getFilesUiVariant,
  recalledCollection,
  rememberCollection,
} from './filesHelpers.js';

export default {
  name: 'BenchFilesCollection',
  mixins: [StateDelayMixin],
  data() {
    return { selectedYear: '' };
  },
  computed: {
    ...mapGetters(['trackConfig']),
    collections() {
      return getFilesCollections(this.trackConfig);
    },
    collectionId() {
      return this.$route.query.collection || recalledCollection();
    },
    selectedCollection() {
      const id = this.collectionId;
      return this.collections.find((item) => item.id === id) || null;
    },
    years() {
      return Object.keys(this.selectedCollection?.years || {});
    },
    yearsVariant() {
      return getFilesUiVariant(this.trackConfig, 'years', 'select');
    },
    buttonsVariant() {
      return getFilesUiVariant(this.trackConfig, 'buttons', 'outline');
    },
    yearFiles() {
      if (!this.selectedCollection || !this.selectedYear) return [];
      return this.selectedCollection.years[this.selectedYear] || [];
    },
    downloadClass() {
      const value = this.buttonsVariant;
      if (value === 'outline') return 'bench-files__btn bench-files__btn--outline btn';
      if (value === 'icon') return 'bench-files__btn bench-files__btn--icon icon-button';
      return 'bench-files__btn bench-files__btn--solid btn';
    },
    downloadLabel() {
      return this.buttonsVariant === 'icon' ? '↓' : 'Скачать';
    },
  },
  methods: {
    fileAddedLabel,
    fileHref,
    formatLabel(file) {
      return String(file.format || '').toUpperCase();
    },
    ensureDomain() {
      const merged = mergeDomainIntoConfig(this.trackConfig, 'files');
      this.$store.commit(PATCH_TRACK_CONFIG, merged);
    },
    chooseYear(year) {
      if (!year) return;
      this.selectedYear = String(year);
      _logActivity(this, {
        type: 'bench_files_select_year',
        year: this.selectedYear,
      });
    },
    download(file) {
      const collection = this.selectedCollection;
      if (!collection || !file) return;
      _logActivity(this, {
        type: 'bench_files_download',
        collection: collection.id,
        year: this.selectedYear,
        format: file.format,
        file: file.file,
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
    if (this.collectionId) {
      rememberCollection(this.collectionId);
    }
    this.applyStateDelay?.();
  },
};
</script>

<style src="@/assets/bench.css"></style>
