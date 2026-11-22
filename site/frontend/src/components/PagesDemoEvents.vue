<template>
  <div class="pages-demo-events">
    <button
      type="button"
      class="pages-demo-events__toggle"
      :aria-expanded="open ? 'true' : 'false'"
      @click="open = !open"
    >
      События
      <span v-if="rows.length">{{ rows.length }}</span>
    </button>
    <aside v-if="open" class="pages-demo-events__panel" aria-label="События">
      <header>
        <strong>События</strong>
        <button type="button" @click="open = false">Скрыть</button>
      </header>
      <label class="pages-demo-events__filter">
        <input v-model="showNoise" type="checkbox" />
        Клики и прокрутка
      </label>
      <p v-if="!visible.length" class="pages-demo-events__empty">
        Действия на странице появятся здесь.
      </p>
      <ol>
        <li
          v-for="row in visible"
          :key="row.id"
          :class="{ target: isTarget(row) }"
        >
          <button type="button" @click="toggle(row.id)">
            <span>{{ timeOf(row) }}</span>
            <b>{{ typeOf(row) }}</b>
            <em>{{ summaryOf(row) }}</em>
          </button>
          <pre v-if="expanded === row.id">{{ pretty(row) }}</pre>
        </li>
      </ol>
    </aside>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import { pagesDemoEventList } from "@/common/pagesDemo";

const NOISE = new Set(["click", "scroll", "keydown", "visibility"]);

export default {
  name: "PagesDemoEvents",
  data() {
    return {
      open: false,
      showNoise: false,
      expanded: null,
      rows: [],
    };
  },
  computed: {
    ...mapGetters(["trackConfig"]),
    targetTypes() {
      const list = this.trackConfig?.test_data?.target_events || [];
      return new Set(list.map((item) => String(item).toLowerCase()));
    },
    visible() {
      const rows = this.showNoise
        ? this.rows
        : this.rows.filter((row) => !NOISE.has(this.typeOf(row)));
      return [...rows].reverse();
    },
  },
  mounted() {
    this.refresh();
    this.onEvents = () => this.refresh();
    window.addEventListener("pages-demo-events", this.onEvents);
  },
  beforeUnmount() {
    window.removeEventListener("pages-demo-events", this.onEvents);
  },
  methods: {
    refresh() {
      this.rows = pagesDemoEventList();
    },
    typeOf(row) {
      if (row.event_name) return String(row.event_name);
      try {
        const data = JSON.parse(row.event_data);
        return data.type ? String(data.type) : "event";
      } catch (error) {
        return "event";
      }
    },
    isTarget(row) {
      return this.targetTypes.has(this.typeOf(row).toLowerCase());
    },
    timeOf(row) {
      const date = new Date(row.event_ts);
      if (Number.isNaN(date.getTime())) return "";
      return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    },
    summaryOf(row) {
      let data = {};
      try {
        data = typeof row.event_data === "string" ? JSON.parse(row.event_data) : (row.event_data || {});
      } catch (error) {
        return "";
      }
      const bits = [data.new_state, data.state_id, data.item_id, data.element]
        .filter((bit) => bit != null && bit !== "");
      if (data.amount != null) bits.push(`×${data.amount}`);
      return bits.join(" · ");
    },
    pretty(row) {
      try {
        const data = typeof row.event_data === "string" ? JSON.parse(row.event_data) : row.event_data;
        return JSON.stringify(data, null, 2);
      } catch (error) {
        return String(row.event_data || "");
      }
    },
    toggle(id) {
      this.expanded = this.expanded === id ? null : id;
    },
  },
};
</script>

<style scoped>
.pages-demo-events__toggle {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 3000;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 0;
  border-radius: 999px;
  padding: 10px 14px;
  background: #3d5a80;
  color: #fff;
  font: inherit;
  font-weight: 700;
  box-shadow: 0 8px 24px rgba(26, 31, 46, 0.28);
  cursor: pointer;
}
.pages-demo-events__toggle span {
  min-width: 1.4em;
  padding: 0 6px;
  border-radius: 999px;
  background: #d4537e;
  font-size: 12px;
  line-height: 1.6;
}
.pages-demo-events__panel {
  position: fixed;
  top: 64px;
  right: 16px;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  width: min(380px, calc(100vw - 32px));
  max-height: calc(100vh - 96px);
  overflow: auto;
  padding: 12px;
  border-radius: 16px;
  background: #fff;
  color: #2c3e50;
  box-shadow: 0 16px 40px rgba(26, 31, 46, 0.24);
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
header button,
.pages-demo-events__panel li button {
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}
.pages-demo-events__filter {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0;
  font-size: 14px;
}
.pages-demo-events__empty {
  margin: 8px 0;
  color: #6b7c93;
}
ol {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
li {
  border-radius: 10px;
  background: #f0f3f7;
}
li.target {
  background: #e5f6ec;
}
li button {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  gap: 8px;
  width: 100%;
  padding: 8px 10px;
  text-align: left;
}
li span { color: #6b7c93; font-size: 12px; }
li b { font-size: 13px; }
li em {
  overflow: hidden;
  color: #3d5166;
  font-style: normal;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
pre {
  margin: 0;
  padding: 0 10px 10px;
  overflow: auto;
  font-size: 11px;
  line-height: 1.4;
}
</style>
