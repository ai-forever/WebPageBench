
<style>
@import "./assets/roboto.css";
@import "./assets/main.css";
@import "./assets/bench.css";
@import "./assets/mock-layout-aliases.css";
@import "./assets/no-promo.css";

main.v-main.bench-rail-layout {
  width: 100%;
  max-width: 1600px;
  margin-left: auto;
  margin-right: auto;
}
</style>

<template>
  <div>
    <v-app>
      <BenchTopNav />
      <v-main :class="mainClass">
        <v-container fluid class="pa-0">
          <router-view></router-view>
        </v-container>
      </v-main>
    </v-app>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import { ActivityTracker } from '@/common/tracker';
import { API_URL } from "@/common/config";
import BenchTopNav from '@/components/BenchTopNav.vue';
import { applyBenchTheme, isBenchAnonymized } from '@/common/benchTheme';

export default {
  name: "App",
  components: { BenchTopNav },
  mixins: [ActivityTracker],
  data: () => ({}),
  methods: {
    goHome() {
      this.$router.push({ name: "main" });
    },
    getImg() {
      return `${API_URL}static/img/logo.png`;
    },
    syncBenchTheme() {
      applyBenchTheme(this.trackConfig);
    },
  },
  computed: {
    ...mapGetters(["userId", "userName", "trackConfig"]),
    mainClass() {
      const name = this.$route?.name || '';
      const classes = [];
      if (name.startsWith('bench_rail_')) {
        classes.push(name === 'bench_rail_search' ? 'bench-rail-layout bench-rail-search-layout' : 'bench-rail-layout');
      }
      if (isBenchAnonymized(this.trackConfig)) {
        classes.push('bench-anonymized');
      }
      return classes.join(' ');
    },
  },
  watch: {
    trackConfig: {
      handler() {
        this.syncBenchTheme();
      },
      deep: true,
    },
  },
  mounted() {
    this.syncBenchTheme();
  },
};
</script>
