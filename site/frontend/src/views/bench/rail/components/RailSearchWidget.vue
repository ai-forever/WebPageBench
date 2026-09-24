<template>
  <div class="rail-search-widget">
    <div class="widget-tabs">
      <button :class="['tab-btn', { active: activeTab === 'tickets' }]" @click="activeTab = 'tickets'">
        <v-icon size="20">mdi-ticket-outline</v-icon>
        <span>БИЛЕТЫ</span>
      </button>
      <button :class="['tab-btn', { active: activeTab === 'hotels' }]" @click="activeTab = 'hotels'">
        <v-icon size="20">mdi-office-building</v-icon>
        <span>ОТЕЛИ</span>
      </button>
    </div>

    <div class="search-form">
      <!-- Native select stations variant -->
      <RailStationNativeSelect
        v-if="stationVariant === 'native_select'"
        :from="form.from"
        :to="form.to"
        :stations="stations"
        :errors="errors"
        @update:from="form.from = $event"
        @update:to="form.to = $event"
        @swap="swapStations"
      />
      <template v-if="stationVariant === 'typeahead'">
      <!-- From Station -->
      <div class="form-field station-field" :class="{ 'has-error': errors.from }" @click.stop="handleFromFieldClick">
        <div class="field-inner">
          <input
            ref="fromInput"
            v-model="form.from"
            type="text"
            :placeholder="form.from ? '' : 'Откуда'"
            @input="onFromInput"
            @click.stop="handleFromFieldClick"
          />
        </div>
        <div v-if="showFromDropdown" class="station-dropdown" @click.stop>
          <div class="dropdown-header">
            <v-icon size="22" color="#ddd">mdi-map-marker-outline</v-icon>
            <span>Город, населённый пункт</span>
          </div>
          <div
            v-for="station in filteredFromStations"
            :key="station.code"
            class="dropdown-item"
            @mousedown.prevent="selectFromStation(station)"
          >
            <v-icon size="22" color="#ddd">mdi-train</v-icon>
            <span>{{ station.name }}</span>
          </div>
        </div>
      </div>

      <div class="swap-btn-container">
        <!-- Swap Button -->
        <button class="swap-btn" @click="swapStations">
          <v-icon size="28">mdi-swap-horizontal</v-icon>
        </button>
      </div>

      <!-- To Station -->
      <div class="form-field station-field" :class="{ 'has-error': errors.to }" @click.stop="handleToFieldClick">
        <div class="field-inner">
          <input
            ref="toInput"
            v-model="form.to"
            type="text"
            :placeholder="form.to ? '' : 'Куда'"
            @input="onToInput"
            @click.stop="handleToFieldClick"
          />
        </div>
        <div v-if="showToDropdown" class="station-dropdown" @click.stop>
          <div class="dropdown-header">
            <v-icon size="22" color="#ddd">mdi-map-marker-outline</v-icon>
            <span>Город, населённый пункт</span>
          </div>
          <div
            v-for="station in filteredToStations"
            :key="station.code"
            class="dropdown-item"
            @mousedown.prevent="selectToStation(station)"
          >
            <v-icon size="22" color="#ddd">mdi-train</v-icon>
            <span>{{ station.name }}</span>
          </div>
        </div>
      </div>
      </template>

      <!-- Alternative date variants -->
      <RailDateNativeInput
        v-if="dateVariant === 'native_input'"
        :departure-date="form.departureDate"
        :return-date="form.returnDate"
        :has-error="errors.departureDate"
        @update:departure-date="form.departureDate = $event"
        @update:return-date="form.returnDate = $event"
      />
      <RailDateTextInput
        v-else-if="dateVariant === 'text_input'"
        :departure-date="form.departureDate"
        :return-date="form.returnDate"
        :has-error="errors.departureDate"
        @update:departure-date="form.departureDate = $event"
        @update:return-date="form.returnDate = $event"
      />

      <template v-else>
      <!-- Departure Date -->
      <div class="form-field date-field" :class="{ 'has-value': form.departureDate, 'has-error': errors.departureDate }">
        <div class="field-inner" @click="openDepartureDatePicker">
          <span v-if="form.departureDate" class="date-value">{{ formatDateShort(form.departureDate) }}</span>
          <span v-else class="field-label">Туда</span>
        </div>
        <button v-if="form.departureDate" class="clear-btn" @click.stop="clearDepartureDate">
          <v-icon size="24">mdi-close</v-icon>
        </button>        <!-- DatePicker Popup - positioned under return date -->
      </div>

      <!-- Return Date -->
      <div class="form-field date-field return-date-field" :class="{ 'has-value': form.returnDate }">
        <div class="field-inner" @click="openReturnDatePicker">
          <span v-if="form.returnDate" class="date-value">{{ formatDateShort(form.returnDate) }}</span>
          <span v-else class="field-label">Обратно</span>
        </div>
        <button v-if="form.returnDate" class="clear-btn" @click.stop="clearReturnDate">
          <v-icon size="24">mdi-close</v-icon>
        </button>
      </div>

      <div v-if="showDatePicker" class="datepicker-container datepicker-floating" @click.stop>
        <RailDatePicker
          :title="datePickerTitle"
          :min-date="datePickerMinDate"
          :start-date="form.departureDate"
          :end-date="form.returnDate"
          :show-no-return="datePickerMode === 'return'"
          @update:model-value="handleDateSelect"
          @no-return="handleNoReturn"
        />
      </div>
      </template>

      <!-- Passengers -->
      <div class="form-field passengers-field">
        <div class="field-inner passengers-toggle" @click="togglePassengersDropdown">
          <v-icon class="passengers-toggle-icon" size="24" color="#999">mdi-account-outline</v-icon>
          <span class="passengers-text">{{ passengersText }}</span>
          <v-icon size="26" color="#555">mdi-chevron-down</v-icon>
        </div>
        <RailPassengersDropdown
          v-if="showPassengersDropdown"
          v-model="form.passengers"
          @close="showPassengersDropdown = false"
        />
      </div>

      <!-- Search Button -->
      <button class="search-btn" @click="search">НАЙТИ</button>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";
import store from "@/store";
import { resolveUiVariant } from "@/bench/ui/useBenchUiVariant";
import RailDatePicker from "./RailDatePicker.vue";
import RailPassengersDropdown from "./RailPassengersDropdown.vue";
import RailDateNativeInput from "@/bench/ui/rail/RailDateNativeInput.vue";
import RailDateTextInput from "@/bench/ui/rail/RailDateTextInput.vue";
import RailStationNativeSelect from "@/bench/ui/rail/RailStationNativeSelect.vue";
import { _logActivity } from "@/common/trackHelper";

const STATIONS = [
  { code: "2000000", name: "Москва" },
  { code: "2004000", name: "Санкт-Петербург" },
  { code: "2060600", name: "Казань" },
  { code: "2060001", name: "Нижний Новгород" },
  { code: "2030000", name: "Адлер" },
  { code: "2050000", name: "Самара" },
  { code: "2034000", name: "Сочи" },
  { code: "2010000", name: "Екатеринбург" },
  { code: "2020000", name: "Новосибирск" },
  { code: "2070000", name: "Краснодар" },
  { code: "2080000", name: "Ростов-на-Дону" },
  { code: "2090000", name: "Воронеж" },
  { code: "2100000", name: "Волгоград" },
  { code: "2110000", name: "Пермь" },
  { code: "2120000", name: "Уфа" },
  { code: "2130000", name: "Челябинск" },
  { code: "2140000", name: "Тюмень" },
  { code: "2150000", name: "Омск" },
  { code: "2160000", name: "Саратов" },
  { code: "2170000", name: "Ярославль" },
];

export default defineComponent({
  name: "RailSearchWidget",
  components: {
    RailDatePicker,
    RailPassengersDropdown,
    RailDateNativeInput,
    RailDateTextInput,
    RailStationNativeSelect,
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        from: "",
        to: "",
        departureDate: null,
        returnDate: null,
        passengers: {
          adults: 1,
          childrenWithSeat: 0,
          childrenWithoutSeat: 0,
          forDisabled: false,
          forLargeFamilies: false,
          pet: false,
          car: false,
          motorcycle: false,
        },
      }),
    },
  },
  emits: ["update:modelValue", "search"],
  data() {
    return {
      activeTab: "tickets",
      form: {
        from: "",
        to: "",
        departureDate: null,
        returnDate: null,
        passengers: {
          adults: 1,
          childrenWithSeat: 0,
          childrenWithoutSeat: 0,
          forDisabled: false,
          forLargeFamilies: false,
          pet: false,
          car: false,
          motorcycle: false,
        },
      },
      showFromDropdown: false,
      showToDropdown: false,
      showDatePicker: false,
      datePickerMode: "departure", // 'departure' or 'return'
      showPassengersDropdown: false,
      stations: STATIONS,
      errors: {
        from: false,
        to: false,
        departureDate: false,
      },
      _syncing: false,
    };
  },
  computed: {
    dateVariant() {
      const cfg = store.getters.trackConfig || {};
      return resolveUiVariant(cfg, "date", "rail");
    },
    stationVariant() {
      const cfg = store.getters.trackConfig || {};
      return resolveUiVariant(cfg, "select_station", "rail");
    },
    today() {
      return new Date();
    },
    filteredFromStations() {
      const query = this.form.from.toLowerCase();
      if (!query) return this.stations.slice(0, 6);
      return this.stations.filter((s) =>
        s.name.toLowerCase().includes(query)
      ).slice(0, 8);
    },
    filteredToStations() {
      const query = this.form.to.toLowerCase();
      if (!query) return this.stations.slice(0, 6);
      return this.stations.filter((s) =>
        s.name.toLowerCase().includes(query)
      ).slice(0, 8);
    },
    datePickerTitle() {
      return this.datePickerMode === "departure" ? "Туда" : "Обратно";
    },
    datePickerMinDate() {
      if (this.datePickerMode === "return" && this.form.departureDate) {
        return this.form.departureDate;
      }
      return this.today;
    },
    passengersText() {
      const total =
        this.form.passengers.adults +
        this.form.passengers.childrenWithSeat +
        this.form.passengers.childrenWithoutSeat;
      if (total === 1) return "1 пассажир";
      if (total >= 2 && total <= 4) return `${total} пассажира`;
      return `${total} пассажиров`;
    },
  },
  watch: {
    modelValue: {
      immediate: true,
      deep: true,
      handler(val) {
        if (!val || this._syncing) return;
        if (this.formsEqual(this.form, val)) return;
        this._syncing = true;
        this.form = {
          ...this.form,
          ...val,
          passengers: val.passengers ? { ...val.passengers } : this.form.passengers,
        };
        this.$nextTick(() => {
          this._syncing = false;
        });
      },
    },
    form: {
      deep: true,
      handler(val) {
        if (this._syncing) return;
        const next = { ...val, passengers: { ...val.passengers } };
        if (this.formsEqual(this.modelValue, next)) return;
        this._syncing = true;
        this.$emit("update:modelValue", next);
        this.$nextTick(() => {
          this._syncing = false;
        });
      },
    },
  },
  mounted() {
    document.addEventListener("click", this.handleOutsideClick);
  },
  beforeUnmount() {
    document.removeEventListener("click", this.handleOutsideClick);
  },
  methods: {
    formsEqual(a, b) {
      if (!a || !b) return false;
      const dateKey = (value) => {
        if (!value) return "";
        const d = value instanceof Date ? value : new Date(value);
        if (isNaN(d.getTime())) return String(value);
        return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      };
      return (
        a.from === b.from &&
        a.to === b.to &&
        dateKey(a.departureDate) === dateKey(b.departureDate) &&
        dateKey(a.returnDate) === dateKey(b.returnDate) &&
        JSON.stringify(a.passengers || {}) === JSON.stringify(b.passengers || {})
      );
    },
    formatDateShort(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = d.getDate();
      const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
      const weekdays = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
      return `${day} ${months[d.getMonth()]}, ${weekdays[d.getDay()]}`;
    },
    formatDateLong(date) {
      if (!date) return "";
      const d = new Date(date);
      const day = String(d.getDate()).padStart(2, "0");
      const month = String(d.getMonth() + 1).padStart(2, "0");
      const year = d.getFullYear();
      return `${day}.${month}.${year}`;
    },
    // Format date as YYYY-MM-DD in LOCAL time (not UTC)
    formatDateISO(date) {
      if (!date) return null;
      const d = date instanceof Date ? date : new Date(date);
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    },
    handleOutsideClick(e) {
      const widget = this.$el;
      if (widget && !widget.contains(e.target)) {
        this.closeAllDropdowns();
      }
    },
    closeAllDropdowns() {
      this.showFromDropdown = false;
      this.showToDropdown = false;
      this.showDatePicker = false;
      this.showPassengersDropdown = false;
    },
    handleFromFieldClick() {
      const wasOpen = this.showFromDropdown;
      this.closeAllDropdowns();
      if (!wasOpen) {
        this.showFromDropdown = true;
      }
      this.$refs.fromInput?.focus();
    },
    handleToFieldClick() {
      this.closeAllDropdowns();
      const wasOpen = this.showToDropdown;
      if (!wasOpen) {
        this.showToDropdown = true;
      }
      this.$refs.toInput?.focus();
    },
    openDepartureDatePicker() {
      this.closeAllDropdowns();
      this.datePickerMode = "departure";
      this.showDatePicker = true;
    },
    openReturnDatePicker() {
      this.closeAllDropdowns();
      this.datePickerMode = "return";
      this.showDatePicker = true;
    },
    togglePassengersDropdown() {
      const wasOpen = this.showPassengersDropdown;
      this.closeAllDropdowns();
      this.showPassengersDropdown = !wasOpen;
    },
    onFromInput() {
      this.showFromDropdown = true;
      this.errors.from = false;
    },
    onToInput() {
      this.showToDropdown = true;
      this.errors.to = false;
    },
    selectFromStation(station) {
      this.form.from = station.name;
      this.errors.from = false;
      this.showFromDropdown = false;
      // Log select_city event
      _logActivity(this, {
        type: "select_city",
        direction: "from",
        field: "from",
        name: station.name,
      });
      // Sequential flow: open "to" dropdown after selecting "from"
      this.showToDropdown = true;
        this.$refs.toInput?.focus();
    },
    selectToStation(station) {
      this.form.to = station.name;
      this.errors.to = false;
      this.showToDropdown = false;
      // Log select_city event
      _logActivity(this, {
        type: "select_city",
        direction: "to",
        field: "to",
        name: station.name,
      });
      // Sequential flow: open departure date picker after selecting "to"
      this.datePickerMode = "departure";
      this.showDatePicker = true;
    },
    swapStations() {
      const temp = this.form.from;
      this.form.from = this.form.to;
      this.form.to = temp;
    },
    handleDateSelect(date) {
      // Capture the date string for logging BEFORE any state changes
      // Use formatDateISO to get local date (not UTC) to avoid timezone issues
      const dateStr = this.formatDateISO(date);
      
      if (this.datePickerMode === "departure") {
        // Log select_date event for departure BEFORE state changes
        _logActivity(this, {
          type: "select_date",
          direction: "departure",
          date: dateStr,
        });
        this.form.departureDate = date;
        this.errors.departureDate = false;
        // If return date is before new departure date, clear it
        if (this.form.returnDate && this.form.returnDate < date) {
          this.form.returnDate = null;
        }
        // Switch to return date selection
        this.datePickerMode = "return";
      } else {
        // Log select_date event for return BEFORE state changes
        _logActivity(this, {
          type: "select_date",
          direction: "return",
          date: dateStr,
        });
        this.form.returnDate = date;
        this.showDatePicker = false;
        // Sequential flow: open passengers dropdown after selecting return date
        this.showPassengersDropdown = true;
      }
    },
    handleNoReturn() {
      this.form.returnDate = null;
      this.showDatePicker = false;
      // Sequential flow: open passengers dropdown after clicking "no return"
      this.showPassengersDropdown = true;
    },
    clearDepartureDate() {
      this.form.departureDate = null;
      this.form.returnDate = null;
    },
    clearReturnDate() {
      this.form.returnDate = null;
    },
    clearErrors() {
      this.errors.from = false;
      this.errors.to = false;
      this.errors.departureDate = false;
    },
    validateForm() {
      this.clearErrors();
      let isValid = true;

      if (!this.form.from || !this.form.from.trim()) {
        this.errors.from = true;
        isValid = false;
      }

      if (!this.form.to || !this.form.to.trim()) {
        this.errors.to = true;
        isValid = false;
      }

      if (!this.form.departureDate) {
        this.errors.departureDate = true;
        isValid = false;
      }

      return isValid;
    },
    search() {
      if (!this.validateForm()) {
        return;
      }
      // Log submit_search event
      const totalPassengers =
        this.form.passengers.adults +
        this.form.passengers.childrenWithSeat +
        this.form.passengers.childrenWithoutSeat;
      _logActivity(this, {
        type: "submit_search",
        city_from: this.form.from,
        city_to: this.form.to,
        date_from: this.formatDateISO(this.form.departureDate),
        date_to: this.formatDateISO(this.form.returnDate),
        passengers_amount: totalPassengers,
      });
      this.$emit("search", this.form);
    },
  },
});
</script>

<style scoped>
.rail-search-widget {
  background: var(--bench-surface-elevated, #fff);
  border-radius: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.widget-tabs {
  display: flex;
  border-bottom: 1px solid #e0e0e0;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  font-size: 14px;
  font-weight: 400;
  color: #666;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.tab-btn.active {
  background: #e21a1a;
  color: #fff;
}

.tab-btn:not(.active):hover {
  background: var(--bench-primary-light, #f5f5f5);
}

.search-form {
  display: flex;
  align-items: stretch;
  position: relative;
}

.form-field {
  position: relative;
  border-right: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  min-inline-size: 0;
}

.form-field:last-of-type {
  border-right: none;
}

.station-field {
  flex: 1.3;
}

.date-field {
  flex: 1;
}

.passengers-field {
  flex: 1.1;
  border-right: none;
}

.field-inner {
  flex: 1;
  padding: 0px 16px;
  cursor: pointer;
  min-height: 56px;
  display: flex;
  align-items: center;
}

.field-inner input {
  width: 100%;
  border: none;
  font-size: 16px;
  color: #000;
  background: transparent;
  outline: none;
}

.field-inner input::placeholder {
  color: #999;
}

.field-label {
  color: #999;
  font-size: 16px;
  pointer-events: none;
  font-weight: 500;
}

.date-value {
  color: #000;
  font-size: 16px;
  font-weight: 500;
}

.clear-btn {
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: #aaa;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  color: #aaa;
}

.swap-btn-container {
  position: relative;
  flex: 0 0 0;
  inline-size: 0;
  z-index: 10;
}

.search-form :deep(.swap-btn),
.swap-btn {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  inline-size: 32px;
  block-size: 32px;
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e0e0e0;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  padding: 0;
}

.search-form :deep(.swap-btn:hover),
.swap-btn:hover {
  color: var(--rail-red, #e21a1a);
  border-color: #ccc;
}

.station-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bench-surface-elevated, #fff);
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  padding-bottom: 10px;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 15px 10px 10px 10px;
  color: #999;
  font-size: 14px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  cursor: pointer;
  font-size: 16px;
}

.dropdown-item:hover {
  background: var(--bench-primary-light, #f5f5f5);
}

.dropdown-item span {
  color: var(--bench-text, #333);
}

.return-date-field {
  position: relative;
}

.datepicker-container {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 200;
}

.passengers-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding-left: 0px;
}

.passengers-toggle .passengers-toggle-icon {
  background: var(--bench-primary-light, #f5f5f5);
  border-radius: 50%;
  padding: 16px;
}

.passengers-text {
  flex: 1;
  font-size: 16px;
  color: #000;
  font-weight: 500;
  padding-left: 5px;
}

.search-btn {
  background: var(--bench-surface-elevated, #fff);
  border: none;
  border-left: 1px solid #e0e0e0;
  color: var(--rail-red);
  font-size: 15px;
  font-weight: 600;
  padding: 10px 28px;
  cursor: pointer;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  min-width: 150px;
  margin-right: -0.5px !important;
}

.search-btn:hover {
  background: var(--rail-red);
  color: #fff;
}

/* Validation error styles */
.form-field.has-error {
  border: 2px solid #e21a1a;
  border-right: 1px solid #e21a1a;
}

.form-field.has-error + .swap-btn-container + .form-field {
  border-left: none;
}

</style>
