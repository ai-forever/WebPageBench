<template>
  <v-row>
    <v-col cols="12" class="text-h5">Конфиг</v-col>
    <v-col>
      <div>Берем конфиг, чтобы начать задание.</div>

      <br /><strong>debug_msg:</strong> {{ debugMsg }}
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG, GET_KV_STORE } from "@/store/actions.type";
import { PATCH_TRACK_CONFIG } from "@/store/mutations.type";
import { mergeDomainIntoConfig } from "@/common/benchTheme";
import { applyDefaultMockLoginFromTrackConfig, clearBenchClientState } from "@/utils/localCache.js";

export default defineComponent({
  name: "StartView",
  data() {
    return {
      API_URL,
      debugMsg: "",
    };
  },
  methods: {
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(async () => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }

          let config = this.trackConfig;
          const benchDomain = config?.test_data?.bench_first_domain;
          if (benchDomain) {
            config = mergeDomainIntoConfig(config, benchDomain);
            this.$store.commit(PATCH_TRACK_CONFIG, config);
            const kvPath = config?.test_data?.kv_store_path;
            if (kvPath) {
              await this.$store.dispatch(GET_KV_STORE, { kvPath });
            }
          }

          const firstStep = this.getFirstStep(config);
          if (!firstStep) {
            this.debugMsg = "No first step found";
            return;
          }

          const viewType = config[firstStep].view_type;
          this.debugMsg = `Going to first step: [${firstStep}]. Type: [${viewType}]`;
          clearBenchClientState();
          applyDefaultMockLoginFromTrackConfig(config);

          setTimeout(() => {
            this.$router.push({
              name: viewType,
              params: { state_id: firstStep, track_id: this.$route.params.track_id },
            });
          }, 100);
        });
    },
    getFirstStep(config) {
      const td = config?.test_data;
      if (td?.bench_first_state) {
        return td.bench_first_state;
      }
      const keys = Object.keys(config).filter((key) => key.startsWith("state_"));
      if (td?.unified_bench && keys.includes("state_hub")) {
        return "state_hub";
      }
      return keys.find((key) => key !== "state_hub") || keys[0] || null;
    },
  },
  computed: {
    ...mapGetters(["trackConfig"]),
  },
  mounted() {
    this.getTrackConfig();
  },
});
</script>
