<template>
  <v-row>
    <v-col cols="12" class="text-h5">Конфиг</v-col>
    <v-col>
      <div>Достаем из конфига тип View для отображения.</div>

      <!-- track config {{ trackConfig }}
      <br />
      
      first step {{ getFirstStep() }} -->

      <br /><strong>debug_msg:</strong> {{ debugMsg }}
    </v-col>
  </v-row>
</template>

<script>
import { defineComponent } from "vue";
import { API_URL } from "@/common/config";
import { mapGetters } from "vuex";
import { GET_TRACK_CONFIG } from "@/store/actions.type";
import { PATCH_TRACK_CONFIG } from "@/store/mutations.type";
import { isUnifiedBench, mergeDomainIntoConfig } from "@/common/benchTheme";
import { legacyToBenchViewType } from "@/common/benchViewTypes";

function inferDomainForState(stateId, trackConfig) {
  if (!stateId || !trackConfig?.domain_configs) return null;
  for (const [domainKey, slice] of Object.entries(trackConfig.domain_configs)) {
    if (slice && slice[stateId]) return domainKey;
    const aliases = slice.state_aliases;
    if (aliases) {
      for (const [legacy, canonical] of Object.entries(aliases)) {
        if (legacy === stateId || canonical === stateId) return domainKey;
      }
    }
  }
  return trackConfig.test_data?.active_bench_domain || null;
}

export default defineComponent({
  name: "StateSelectorView",
  components: {},
  data() {
    return {
      API_URL,
      debugMsg: "",
    };
  },
  methods: {
    getTrackConfig() {
      const stateId = this.$route.params.state_id;
      const trackId = this.$route.params.track_id;
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId })
        .then(() => {
          let cfg = this.trackConfig;
          if (!cfg || Object.keys(cfg).length === 0) {
            this.$router.push({ name: "not_found" });
            return;
          }
          if (isUnifiedBench(cfg)) {
            const domain = inferDomainForState(stateId, cfg);
            if (domain) {
              cfg = mergeDomainIntoConfig(cfg, domain);
              this.$store.commit(PATCH_TRACK_CONFIG, cfg);
            }
          }
          const stateDef = cfg[stateId];
          if (!stateDef) {
            this.$router.push({ name: "state_not_found" });
            return;
          }
          const viewType = legacyToBenchViewType(stateDef.view_type);
          this.$router.push({
            name: viewType,
            params: { state_id: stateId, track_id: trackId },
          });
        });
    },
    getFirstStep() {
      return this.trackConfig ? Object.keys(this.trackConfig)[0] : null;
    },
  },
  computed: {
    ...mapGetters(["trackConfig"]),
  },
  watch: {},
  mounted() {
    // this.$router.push({ name: "type_1", params: { state_id: 'state_1', track_id: 'test_track' } });
    this.getTrackConfig();
  },
  components: {
  },
});
</script>
