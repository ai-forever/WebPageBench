<template>
  <div class="rail-datepicker" @click.stop>
    <div class="datepicker-header">
      <span class="header-title">{{ title }}</span>
      <button class="nav-btn" @click="nextMonths">
        <v-icon size="20">mdi-arrow-right</v-icon>
      </button>
    </div>

    <div class="datepicker-months">
      <div v-for="(month, idx) in visibleMonths" :key="idx" class="month-block">
        <div class="month-title">{{ month.name }} {{ month.year }}</div>
        <div class="weekdays">
          <span v-for="(day, i) in weekdays" :key="day" :class="{ weekend: i >= 5 }">{{ day }}</span>
        </div>
        <div class="days-grid">
          <template v-for="(week, weekIdx) in month.weeks" :key="weekIdx">
            <div
              v-for="(day, dayIdx) in week"
              :key="`${weekIdx}-${dayIdx}`"
              :class="getDayClass(day, dayIdx)"
              @click="day.date && selectDate(day.date)"
            >
              <span v-if="day.date" class="day-number">{{ day.day }}</span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <div v-if="showNoReturn" class="datepicker-footer">
      <button class="no-return-btn" @click="$emit('no-return')">
        Обратный билет не нужен
      </button>
    </div>
  </div>
</template>

<script>
import { defineComponent } from "vue";

export default defineComponent({
  name: "RailDatePicker",
  props: {
    modelValue: {
      type: Date,
      default: null,
    },
    minDate: {
      type: Date,
      default: () => new Date(),
    },
    startDate: {
      type: Date,
      default: null,
    },
    endDate: {
      type: Date,
      default: null,
    },
    title: {
      type: String,
      default: "Туда",
    },
    showNoReturn: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["update:modelValue", "close", "no-return"],
  data() {
    return {
      startMonthOffset: 0,
      weekdays: ["пн", "вт", "ср", "чт", "пт", "сб", "вс"],
      monthNames: [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
      ],
    };
  },
  computed: {
    visibleMonths() {
      const months = [];
      const today = new Date();
      const startMonth = today.getMonth() + this.startMonthOffset;
      const startYear = today.getFullYear();

      for (let i = 0; i < 3; i++) {
        const month = (startMonth + i) % 12;
        const yearOffset = Math.floor((startMonth + i) / 12);
        const year = startYear + yearOffset;
        months.push(this.generateMonth(year, month));
      }

      return months;
    },
  },
  methods: {
    generateMonth(year, month) {
      const firstDay = new Date(year, month, 1);
      const lastDay = new Date(year, month + 1, 0);
      const daysInMonth = lastDay.getDate();

      let startDayOfWeek = firstDay.getDay();
      startDayOfWeek = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;

      const weeks = [];
      let currentWeek = [];

      for (let i = 0; i < startDayOfWeek; i++) {
        currentWeek.push({ date: null, day: null });
      }

      for (let day = 1; day <= daysInMonth; day++) {
        currentWeek.push({
          date: new Date(year, month, day),
          day: day,
        });

        if (currentWeek.length === 7) {
          weeks.push(currentWeek);
          currentWeek = [];
        }
      }

      if (currentWeek.length > 0) {
        while (currentWeek.length < 7) {
          currentWeek.push({ date: null, day: null });
        }
        weeks.push(currentWeek);
      }

      return {
        name: this.monthNames[month],
        year: year,
        weeks: weeks,
      };
    },
    getDayClass(day, dayIdx) {
      const classes = ["day-cell"];

      if (!day.date) {
        classes.push("empty");
        return classes;
      }

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const minDate = new Date(this.minDate);
      minDate.setHours(0, 0, 0, 0);

      const dayDate = new Date(day.date);
      dayDate.setHours(0, 0, 0, 0);

      // Weekend check (Saturday = index 5, Sunday = index 6)
      if (dayIdx >= 5) {
        classes.push("weekend");
      }

      if (dayDate < minDate) {
        classes.push("disabled");
      }

      // Check if in range
      if (this.startDate && this.endDate) {
        const start = new Date(this.startDate);
        start.setHours(0, 0, 0, 0);
        const end = new Date(this.endDate);
        end.setHours(0, 0, 0, 0);

        if (dayDate > start && dayDate < end) {
          classes.push("in-range");
        }
      }

      // Check if selected (start or end date)
      if (this.startDate) {
        const start = new Date(this.startDate);
        start.setHours(0, 0, 0, 0);
        if (dayDate.getTime() === start.getTime()) {
          classes.push("selected", "range-start");
        }
      }

      if (this.endDate) {
        const end = new Date(this.endDate);
        end.setHours(0, 0, 0, 0);
        if (dayDate.getTime() === end.getTime()) {
          classes.push("selected", "range-end");
        }
      }

      // Single selection (modelValue)
      if (this.modelValue && !this.startDate && !this.endDate) {
        const selected = new Date(this.modelValue);
        selected.setHours(0, 0, 0, 0);
        if (dayDate.getTime() === selected.getTime()) {
          classes.push("selected");
        }
      }

      return classes;
    },
    selectDate(date) {
      const minDate = new Date(this.minDate);
      minDate.setHours(0, 0, 0, 0);

      const selectedDate = new Date(date);
      selectedDate.setHours(0, 0, 0, 0);

      if (selectedDate < minDate) {
        return;
      }

      this.$emit("update:modelValue", date);
    },
    nextMonths() {
      this.startMonthOffset += 3;
    },
    prevMonths() {
      if (this.startMonthOffset >= 3) {
        this.startMonthOffset -= 3;
      }
    },
  },
});
</script>

<style scoped>
.rail-datepicker {
  position: absolute;
  top: 100%;
  left: 0;
  background: #fff;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  width: 940px;
}

.datepicker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.header-title {
  font-size: 16px;
  font-weight: 400;
  color: #333;
  flex: 1;
  text-align: center;
}

.nav-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: #333;
}

.nav-btn:hover {
  color: #e21a1a;
}

.datepicker-months {
  display: flex;
  padding: 16px 12px;
}

.month-block {
  flex: 1;
  padding: 0 8px;
}

.month-title {
  font-size: 14px;
  font-weight: 400;
  color: #333;
  margin-bottom: 12px;
  text-align: center;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 4px;
}

.weekdays span {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 4px 0;
  text-transform: lowercase;
}

.weekdays span.weekend {
  color: #e21a1a;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.day-cell {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  min-height: 32px;
}

.day-cell:hover:not(.disabled):not(.empty) {
  background: #f5f5f5;
}

.day-cell.empty {
  cursor: default;
}

.day-cell.disabled {
  pointer-events: none;
  cursor: not-allowed;
}

.day-cell.disabled .day-number {
  color: #ccc;
}

.day-cell.weekend:not(.selected) .day-number {
  color: #e21a1a;
}

.day-cell.in-range {
  background: #fdefef;
}

.day-cell.selected {
  background: #e21a1a;
  border-radius: 50%;
}

.day-cell.selected .day-number {
  color: #fff;
}

.day-cell.selected.weekend .day-number {
  color: #fff;
}

.day-cell.range-start {
  border-radius: 50%;
  background: #e21a1a;
}

.day-cell.range-end {
  border-radius: 50%;
  background: #e21a1a;
}

.day-number {
  font-size: 14px;
  color: #333;
  position: relative;
  z-index: 1;
}

.datepicker-footer {
  padding: 12px 16px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.no-return-btn {
  background: none;
  border: 1px solid #e21a1a;
  color: #e21a1a;
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.no-return-btn:hover {
  background: #e21a1a;
  color: #fff;
}
</style>
