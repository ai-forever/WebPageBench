
<template>
  <div class="menu-bar">
    <div class="container">
      <v-btn
        v-for="(item, index) in items"
        :key="index"
        class="menu-item"
        :class="{ orange: item.orange, active: isActive(item) }"
        variant="text"
        @click="onItemClick(item)"
      >
        {{ item.caption }}
      </v-btn>
    </div>
  </div>
</template>

<script>
import { legacyToBenchViewType } from '@/common/benchViewTypes';
import { ensureBenchDomainMerged, pushBenchRoute, resolveBenchDomain } from '@/common/benchNavigation';

export default {
  props: {
    items: { type: Array, default: () => [] },
  },
  methods: {
    isActive(item) {
      if (!item) return false;
      const stateId = item.to_state || item.category_id;
      if (!stateId) return false;
      return String(this.$route.params.state_id) === String(stateId);
    },
    onItemClick(item) {
      if (!item || !item.to_view_type) return;
      const routeName = legacyToBenchViewType(item.to_view_type);
      const domain = resolveBenchDomain(routeName);
      if (domain) {
        ensureBenchDomainMerged(domain);
      }
      pushBenchRoute(this.$router, {
        name: routeName,
        stateId: item.to_state || item.category_id,
        trackId: this.$route.params.track_id,
      });
    },
  },
};
</script>

<style scoped>
.menu-bar .container {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.menu-bar .container::-webkit-scrollbar {
  display: none;
}

.menu-item {
  flex-shrink: 0;
  text-transform: none;
  cursor: pointer;
  white-space: nowrap;
}

.menu-item.active {
  background: rgba(255, 255, 255, 0.14);
  border-radius: 6px;
}

.menu-item :deep(.v-btn__content) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
</style>