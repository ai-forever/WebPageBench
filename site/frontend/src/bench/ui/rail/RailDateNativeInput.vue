<template>
  <div class="bench-rail-date-native">
    <div class="form-field date-field native-date" :class="{ 'has-value': departureIso, 'has-error': hasError }">
      <div class="field-inner">
        <label class="native-label">Туда</label>
        <input
          type="date"
          lang="ru"
          class="native-date-input"
          :value="departureIso"
          @input="onDeparture"
          @keydown="onTyped($event, 'departure')"
          @paste="onPaste($event, 'departure')"
        />
      </div>
    </div>
    <div class="form-field date-field native-date" :class="{ 'has-value': returnIso }">
      <div class="field-inner">
        <label class="native-label">Обратно</label>
        <input
          type="date"
          lang="ru"
          class="native-date-input"
          :value="returnIso"
          @input="onReturn"
          @keydown="onTyped($event, 'return')"
          @paste="onPaste($event, 'return')"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { _logActivity } from '@/common/trackHelper';

export default {
  name: 'RailDateNativeInput',
  props: {
    departureDate: { type: [Date, String, null], default: null },
    returnDate: { type: [Date, String, null], default: null },
    hasError: { type: Boolean, default: false },
  },
  emits: ['update:departureDate', 'update:returnDate'],
  data() {
    return {
      typedDep: '',
      typedRet: '',
      lastDepIso: '',
      lastRetIso: '',
    };
  },
  computed: {
    departureIso() {
      return this.departureDate ? this.toIso(this.departureDate) : '';
    },
    returnIso() {
      return this.returnDate ? this.toIso(this.returnDate) : '';
    },
  },
  methods: {
    toIso(date) {
      const d = this.asLocalDate(date);
      if (!d) return '';
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${y}-${m}-${day}`;
    },
    asLocalDate(date) {
      if (!date) return null;
      if (date instanceof Date) {
        return isNaN(date.getTime()) ? null : date;
      }
      return this.fromFlexible(String(date));
    },
    partsToIso(year, month, day) {
      const y = Number(year);
      const m = Number(month);
      const d = Number(day);
      if (!Number.isFinite(y) || y < 2000 || m < 1 || m > 12 || d < 1 || d > 31) return null;
      const dt = new Date(y, m - 1, d);
      dt.setFullYear(y);
      if (dt.getFullYear() !== y || dt.getMonth() !== m - 1 || dt.getDate() !== d) return null;
      return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    },
    fromFlexible(text) {
      const s = String(text).trim();
      let m = s.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
      if (m) {
        const iso = this.partsToIso(m[3], m[2], m[1]);
        return iso ? this.fromIso(iso) : null;
      }
      m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (m) {
        const iso = this.partsToIso(m[1], m[2], m[3]);
        return iso ? this.fromIso(iso) : null;
      }
      m = s.match(/^(\d{2})(\d{2})(\d{4})$/);
      if (m) {
        const iso = this.partsToIso(m[3], m[2], m[1]);
        return iso ? this.fromIso(iso) : null;
      }
      return null;
    },
    fromIso(str) {
      if (!str) return null;
      const [y, m, d] = str.split('-').map(Number);
      if (!y || y < 2000) return null;
      const date = new Date(y, m - 1, d);
      date.setFullYear(y);
      return isNaN(date.getTime()) ? null : date;
    },
    commit(which, iso) {
      const d = this.fromIso(iso);
      if (!d) return false;
      if (which === 'departure') {
        if (this.lastDepIso === iso) return true;
        this.lastDepIso = iso;
        _logActivity(this, { type: 'select_date', direction: 'departure', date: iso });
        this.$emit('update:departureDate', d);
      } else {
        if (this.lastRetIso === iso) return true;
        this.lastRetIso = iso;
        _logActivity(this, { type: 'select_date', direction: 'return', date: iso });
        this.$emit('update:returnDate', d);
      }
      return true;
    },
    applyTyped(which, text, inputEl, preventEvent) {
      const parsed = this.fromFlexible(text);
      if (!parsed) return false;
      const iso = this.toIso(parsed);
      if (preventEvent) preventEvent.preventDefault();
      if (inputEl) inputEl.value = iso;
      if (which === 'departure') this.typedDep = '';
      else this.typedRet = '';
      return this.commit(which, iso);
    },
    onTyped(e, which) {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const key = e.key;
      if (key === 'Backspace') {
        if (which === 'departure') this.typedDep = this.typedDep.slice(0, -1);
        else this.typedRet = this.typedRet.slice(0, -1);
        return;
      }
      if (key === 'Tab' || key === 'Enter' || key === 'Escape') {
        const buf = which === 'departure' ? this.typedDep : this.typedRet;
        this.applyTyped(which, buf, e.target, null);
        return;
      }
      if (!/^\d$/.test(key) && key !== '.' && key !== '-' && key !== '/') return;
      if (which === 'departure') this.typedDep += key;
      else this.typedRet += key;
      const buf = which === 'departure' ? this.typedDep : this.typedRet;
      this.applyTyped(which, buf, e.target, e);
    },
    onPaste(e, which) {
      const text = e.clipboardData && e.clipboardData.getData('text');
      if (!text) return;
      this.applyTyped(which, text, e.target, e);
    },
    onDeparture(e) {
      const d = this.fromIso(e.target.value) || this.fromFlexible(e.target.value);
      if (!d) return;
      this.commit('departure', this.toIso(d));
    },
    onReturn(e) {
      const val = e.target.value;
      if (!val) {
        this.$emit('update:returnDate', null);
        return;
      }
      const d = this.fromIso(val) || this.fromFlexible(val);
      if (!d) return;
      this.commit('return', this.toIso(d));
    },
  },
};
</script>

<style scoped>
.bench-rail-date-native {
  display: contents;
}

.native-date .field-inner {
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.native-label {
  font-size: 12px;
  color: #888;
}

.native-date-input {
  border: none;
  outline: none;
  font-size: 15px;
  font-weight: 500;
  background: transparent;
  inline-size: 100%;
  color: #333;
}
</style>
