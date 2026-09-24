export const StateDelayMixin = {
  data() {
    return {
      contentReady: false,
      delayTimeout: null,
    };
  },
  methods: {
    applyStateDelay() {
      if (this.delayTimeout) {
        clearTimeout(this.delayTimeout);
        this.delayTimeout = null;
      }

      const delay = this.getStateDelay();
      
      if (delay > 0) {
        this.contentReady = false;
        this.delayTimeout = setTimeout(() => {
          this.contentReady = true;
          this.delayTimeout = null;
        }, delay * 1000);
      } else {
        this.contentReady = true;
      }
    },

    getStateDelay() {
      try {
        const stateId = this.$route && this.$route.params && this.$route.params.state_id;
        const trackConfig = this.$store && this.$store.getters && this.$store.getters.trackConfig;
        
        if (!stateId || !trackConfig || !trackConfig[stateId]) {
          return 0;
        }

        const stateConfig = trackConfig[stateId];
        const delay = stateConfig.delay;

        return typeof delay === 'number' && delay >= 0 ? delay : 0;
      } catch (e) {
        console.error('Error getting state delay:', e);
        return 0;
      }
    },
  },
  watch: {
    '$route.params.state_id'(newStateId, oldStateId) {
      if (newStateId !== oldStateId) {
        this.applyStateDelay();
      }
    },
  },
  beforeUnmount() {
    if (this.delayTimeout) {
      clearTimeout(this.delayTimeout);
      this.delayTimeout = null;
    }
  },
};

