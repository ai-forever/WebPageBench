<template>
  <div class="rail-passengers-dropdown" @click.stop>
    <div class="dropdown-section">
      <div class="section-title">Пассажиры</div>

      <div class="passenger-row">
        <span class="passenger-label">Взрослый</span>
        <div class="counter">
          <button
            class="counter-btn"
            :disabled="localValue.adults <= 1"
            @click="decrementAdults"
          >
            <v-icon size="14">mdi-minus</v-icon>
          </button>
          <span class="counter-value">{{ localValue.adults }}</span>
          <button
            class="counter-btn"
            :disabled="totalPassengers >= 4"
            @click="incrementAdults"
          >
            <v-icon size="14">mdi-plus</v-icon>
          </button>
        </div>
      </div>

      <div class="passenger-row">
        <span class="passenger-label">Ребёнок с местом</span>
        <div class="counter">
          <button
            class="counter-btn"
            :disabled="localValue.childrenWithSeat <= 0"
            @click="decrementChildrenWithSeat"
          >
            <v-icon size="14">mdi-minus</v-icon>
          </button>
          <span class="counter-value">{{ localValue.childrenWithSeat }}</span>
          <button
            class="counter-btn"
            :disabled="totalPassengers >= 4"
            @click="incrementChildrenWithSeat"
          >
            <v-icon size="14">mdi-plus</v-icon>
          </button>
        </div>
      </div>

      <div class="passenger-row">
        <div class="passenger-label-group">
          <span class="passenger-label">Ребёнок без места</span>
          <span class="passenger-hint">от 0 до 5 лет</span>
        </div>
        <div class="counter">
          <button
            class="counter-btn"
            :disabled="localValue.childrenWithoutSeat <= 0"
            @click="decrementChildrenWithoutSeat"
          >
            <v-icon size="14">mdi-minus</v-icon>
          </button>
          <span class="counter-value">{{ localValue.childrenWithoutSeat }}</span>
          <button
            class="counter-btn"
            :disabled="localValue.childrenWithoutSeat >= localValue.adults"
            @click="incrementChildrenWithoutSeat"
          >
            <v-icon size="14">mdi-plus</v-icon>
          </button>
        </div>
      </div>
    </div>

    <div class="dropdown-section">
      <div class="section-title">Места</div>

      <div class="checkbox-row">
        <span class="checkbox-label">Для инвалида</span>
        <label class="toggle-switch">
          <input v-model="localValue.forDisabled" type="checkbox" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="checkbox-row">
        <span class="checkbox-label">Для многодетных семей</span>
        <label class="toggle-switch">
          <input v-model="localValue.forLargeFamilies" type="checkbox" />
          <span class="slider"></span>
        </label>
      </div>
    </div>

    <div class="dropdown-section">
      <div class="section-title">Багаж</div>

      <div class="checkbox-row">
        <div class="checkbox-label-group">
          <span class="checkbox-label">Животное</span>
          <span class="checkbox-hint">с пассажиром или без</span>
        </div>
        <label class="toggle-switch">
          <input v-model="localValue.pet" type="checkbox" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="checkbox-row">
        <div class="checkbox-label-group">
          <span class="checkbox-label">Автомобиль</span>
          <span class="checkbox-hint">в автовозе</span>
        </div>
        <label class="toggle-switch">
          <input v-model="localValue.car" type="checkbox" />
          <span class="slider"></span>
        </label>
      </div>

      <div class="checkbox-row">
        <div class="checkbox-label-group">
          <span class="checkbox-label">Мотоцикл</span>
          <span class="checkbox-hint">в автовозе</span>
        </div>
        <label class="toggle-switch">
          <input v-model="localValue.motorcycle" type="checkbox" />
          <span class="slider"></span>
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailPassengersDropdown",
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        adults: 1,
        childrenWithSeat: 0,
        childrenWithoutSeat: 0,
        forDisabled: false,
        forLargeFamilies: false,
        pet: false,
        car: false,
        motorcycle: false,
      }),
    },
  },
  emits: ["update:modelValue", "close"],
  data() {
    return {
      localValue: {
        adults: 1,
        childrenWithSeat: 0,
        childrenWithoutSeat: 0,
        forDisabled: false,
        forLargeFamilies: false,
        pet: false,
        car: false,
        motorcycle: false,
      },
    };
  },
  computed: {
    totalPassengers() {
      return (
        this.localValue.adults +
        this.localValue.childrenWithSeat +
        this.localValue.childrenWithoutSeat
      );
    },
  },
  watch: {
    modelValue: {
      immediate: true,
      handler(val) {
        // Guard against our own emit coming back: the deep watcher below emits a
        // fresh object on every change, v-model writes it back here, and copying
        // it into localValue would make that watcher fire again — an endless
        // emit/copy loop that spins the renderer until the tab crashes
        // (Playwright: "Target crashed" on the next screenshot). Only adopt a
        // value that actually differs from what we already hold.
        if (!val || JSON.stringify(val) === JSON.stringify(this.localValue)) {
          return;
        }
        this.localValue = { ...val };
      },
    },
    localValue: {
      deep: true,
      handler(val) {
        // Emit a copy to ensure reactivity in parent
        this.$emit("update:modelValue", { ...val });
      },
    },
  },
  methods: {
    incrementAdults() {
      if (this.totalPassengers < 4) {
        this.localValue.adults++;
      }
    },
    decrementAdults() {
      if (this.localValue.adults > 1) {
        this.localValue.adults--;
        if (this.localValue.childrenWithoutSeat > this.localValue.adults) {
          this.localValue.childrenWithoutSeat = this.localValue.adults;
        }
      }
    },
    incrementChildrenWithSeat() {
      if (this.totalPassengers < 4) {
        this.localValue.childrenWithSeat++;
      }
    },
    decrementChildrenWithSeat() {
      if (this.localValue.childrenWithSeat > 0) {
        this.localValue.childrenWithSeat--;
      }
    },
    incrementChildrenWithoutSeat() {
      if (this.localValue.childrenWithoutSeat < this.localValue.adults) {
        this.localValue.childrenWithoutSeat++;
      }
    },
    decrementChildrenWithoutSeat() {
      if (this.localValue.childrenWithoutSeat > 0) {
        this.localValue.childrenWithoutSeat--;
      }
    },
  },
});
</script>

<style scoped>
.rail-passengers-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: #fff;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  min-width: 360px;
  font-family: 'IBM Plex Sans', Arial, Helvetica, sans-serif;
}

.rail-passengers-dropdown .section-title {
  font-size: 20px !important;
  font-weight: 700;
}

.rail-passengers-dropdown .passenger-label {
  font-size: 16px !important;
  font-weight: 400;
  color: #000;
}

.rail-passengers-dropdown .checkbox-label{
  font-size: 16px !important;
  font-weight: 400;
  color: #000;
}

.dropdown-section {
  padding: 14px 16px 0px 16px;
}

.dropdown-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 10px;
}

.passenger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.passenger-label {
  font-size: 14px;
  color: #333;
}

.passenger-label-group {
  display: flex;
  flex-direction: column;
}

.passenger-hint {
  font-size: 11px;
  color: #999;
  margin-top: 1px;
}

.counter {
  display: flex;
  align-items: center;
  gap: 10px;
}

.counter-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid #e0e0e0;
  background: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.counter-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #ccc;
}

.counter-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.counter-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  min-width: 16px;
  text-align: center;
}

.checkbox-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
}

.checkbox-label {
  font-size: 14px;
  color: #333;
}

.checkbox-label-group {
  display: flex;
  flex-direction: column;
}

.checkbox-hint {
  font-size: 11px;
  color: #999;
  margin-top: 1px;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.25s;
  border-radius: 22px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.25s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #e21a1a;
}

input:checked + .slider:before {
  transform: translateX(18px);
}
</style>
