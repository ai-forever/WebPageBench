<template>
  <div class="bench-rail-station-native">
    <div class="form-field station-field native-station" :class="{ 'has-error': errors.from }">
      <div class="field-inner">
        <label class="native-label">Откуда</label>
        <select class="native-select" :value="fromCode" @change="onFromChange">
          <option value="" disabled>Выберите станцию</option>
          <option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option>
        </select>
      </div>
    </div>
    <div class="swap-btn-container">
      <button class="swap-btn" type="button" @click="$emit('swap')">
        <v-icon size="28">mdi-swap-horizontal</v-icon>
      </button>
    </div>
    <div class="form-field station-field native-station" :class="{ 'has-error': errors.to }">
      <div class="field-inner">
        <label class="native-label">Куда</label>
        <select class="native-select" :value="toCode" @change="onToChange">
          <option value="" disabled>Выберите станцию</option>
          <option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script>
import { _logActivity } from '@/common/trackHelper';

export default {
  name: 'RailStationNativeSelect',
  props: {
    from: { type: String, default: '' },
    to: { type: String, default: '' },
    stations: { type: Array, required: true },
    errors: { type: Object, default: () => ({ from: false, to: false }) },
  },
  emits: ['update:from', 'update:to', 'swap'],
  computed: {
    fromCode() {
      const s = this.stations.find((x) => x.name === this.from);
      return s?.code || '';
    },
    toCode() {
      const s = this.stations.find((x) => x.name === this.to);
      return s?.code || '';
    },
  },
  methods: {
    onFromChange(e) {
      const code = e.target.value;
      const station = this.stations.find((s) => s.code === code);
      if (!station) return;
      _logActivity(this, { type: 'select_city', direction: 'from', field: 'from', name: station.name });
      this.$emit('update:from', station.name);
    },
    onToChange(e) {
      const code = e.target.value;
      const station = this.stations.find((s) => s.code === code);
      if (!station) return;
      _logActivity(this, { type: 'select_city', direction: 'to', field: 'to', name: station.name });
      this.$emit('update:to', station.name);
    },
  },
};
</script>

<style scoped>
.bench-rail-station-native {
  display: contents;
}

.native-station .field-inner {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.native-label {
  font-size: 12px;
  color: #888;
}

.native-select {
  border: none;
  outline: none;
  font-size: 15px;
  font-weight: 500;
  background: transparent;
  inline-size: 100%;
  cursor: pointer;
}
</style>
