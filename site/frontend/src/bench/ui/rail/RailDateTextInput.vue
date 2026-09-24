<template>
  <div class="bench-rail-date-text">
    <div class="form-field date-field text-date" :class="{ 'has-error': hasError }">
      <div class="field-inner">
        <span class="field-label">Туда</span>
        <input
          v-model="depText"
          class="text-date-input"
          type="text"
          inputmode="numeric"
          placeholder="ДД.ММ.ГГГГ"
          @input="commitDeparture"
          @blur="commitDeparture"
          @keydown.enter="commitDeparture"
        />
      </div>
    </div>
    <div class="form-field date-field text-date">
      <div class="field-inner">
        <span class="field-label">Обратно</span>
        <input
          v-model="retText"
          class="text-date-input"
          type="text"
          inputmode="numeric"
          placeholder="ДД.ММ.ГГГГ"
          @input="commitReturn"
          @blur="commitReturn"
          @keydown.enter="commitReturn"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { _logActivity } from '@/common/trackHelper';

export default {
  name: 'RailDateTextInput',
  props: {
    departureDate: { type: [Date, String, null], default: null },
    returnDate: { type: [Date, String, null], default: null },
    hasError: { type: Boolean, default: false },
  },
  emits: ['update:departureDate', 'update:returnDate'],
  data() {
    return {
      depText: '',
      retText: '',
      lastDepIso: '',
      lastRetIso: '',
    };
  },
  watch: {
    departureDate: {
      immediate: true,
      handler(v) { this.depText = this.formatRu(v); },
    },
    returnDate: {
      immediate: true,
      handler(v) { this.retText = this.formatRu(v); },
    },
  },
  methods: {
    formatRu(v) {
      if (!v) return '';
      const d = v instanceof Date ? v : this.parseRu(String(v));
      if (!d || isNaN(d.getTime())) return '';
      const dd = String(d.getDate()).padStart(2, '0');
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      return `${dd}.${mm}.${d.getFullYear()}`;
    },
    parseRu(text) {
      const s = String(text).trim();
      let m = s.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
      if (m) return this.fromParts(m[3], m[2], m[1]);
      m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (m) return this.fromParts(m[1], m[2], m[3]);
      m = s.match(/^(\d{2})(\d{2})(\d{4})$/);
      if (m) return this.fromParts(m[3], m[2], m[1]);
      return null;
    },
    fromParts(year, month, day) {
      const y = Number(year);
      const mo = Number(month);
      const d = Number(day);
      if (!Number.isFinite(y) || y < 2000 || mo < 1 || mo > 12 || d < 1 || d > 31) return null;
      const dt = new Date(y, mo - 1, d);
      dt.setFullYear(y);
      if (dt.getFullYear() !== y || dt.getMonth() !== mo - 1 || dt.getDate() !== d) return null;
      return dt;
    },
    toIso(d) {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    },
    commitDeparture() {
      const d = this.parseRu(this.depText);
      if (!d) return;
      const iso = this.toIso(d);
      if (this.lastDepIso === iso) return;
      this.lastDepIso = iso;
      _logActivity(this, { type: 'select_date', direction: 'departure', date: iso });
      this.$emit('update:departureDate', d);
    },
    commitReturn() {
      const d = this.parseRu(this.retText);
      if (!d) return;
      const iso = this.toIso(d);
      if (this.lastRetIso === iso) return;
      this.lastRetIso = iso;
      _logActivity(this, { type: 'select_date', direction: 'return', date: iso });
      this.$emit('update:returnDate', d);
    },
  },
};
</script>

<style scoped>
.bench-rail-date-text {
  display: contents;
}

.text-date-input {
  border: none;
  outline: none;
  font-size: 15px;
  font-weight: 500;
  background: transparent;
  inline-size: 100%;
}
</style>
