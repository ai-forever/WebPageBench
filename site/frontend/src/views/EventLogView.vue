<template>
  <div class="event-log">
    <div class="page-header">
      <h1 class="page-title">Event Log</h1>
      <v-switch
        v-model="showTargetsOnly"
        inset
        hide-details
        density="compact"
        :disabled="!targetEvents.length"
        :label="targetEvents.length ? 'Only target events' : 'Only target events (no targets)'"
      />
    </div>
    <v-card class="event-log-card" elevation="2">
      <v-card-title>
        Events for Track: {{ $route.params.track_id }}
      </v-card-title>
      <v-card-subtitle>
        Time between first and last target event: {{ targetEventsSpan }}
      </v-card-subtitle>

      <!-- {{ trackConfig.test_data.target_events }} -->
      
      <!-- {{ sortedEvents[0] }} -->
      <!-- { "event_data": "{\"type\":\"state_changed\",\"new_state\":\"bench_books_basket\",\"new_path\":\"/ecommerce_basket_any_product/state_basket/bench_books_basket\",\"query\":{}}", "event_id": "d80b0b1e-9fa4-4f12-be47-004502b476c9", "event_name": "state_changed", "event_ts": "2025-09-25_08:45:30", "id": 2 } -->

      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="processedEvents"
          :items-per-page="100"
          class="elevation-0"
          :sort-by="[{ key: 'id', order: 'desc' }]"
          :item-class="getRowClass"
        >
          <template v-slot:[`item.event_name`]="{ item }">
            <span :class="{ 'target-type': isTargetEvent(item) }">{{ getEventType(item) }}</span>
          </template>
          <template v-slot:[`item.time`]="{ item }">
            <span>{{ item.time }}</span>
          </template>
          <template v-slot:[`item.event_data`]="{ item }">
            <pre>{{ formatEventData(item.event_data) }}</pre>
          </template>
          <!-- <template v-slot:item.event_ts="{ item }">
            {{ formatDate(item.event_ts) }}
          </template> -->
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { GET_EVENTS, GET_TRACK_CONFIG } from "@/store/actions.type";

export default {
  name: 'EventLogView',
  data() {
    return {
      headers: [
        { text: 'Event ID', value: 'id' , sortable: true},
        { text: 'Event Name', value: 'event_name' },
        { text: 'Time', value: 'time' },
        { text: 'Event Data', value: 'event_data' },
        { text: 'Timestamp', value: 'event_ts' }
      ],
      refreshInterval: null,
      showTargetsOnly: false
    };
  },
  computed: {
    ...mapGetters(['events', 'trackConfig']),
    targetEvents() {
      const list = (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.target_events) || [];
      if (Array.isArray(list)) {
        return list.map(e => String(e).toLowerCase());
      }
      if (typeof list === 'string') {
        return list.split(',').map(e => e.trim().toLowerCase()).filter(Boolean);
      }
      return [];
    },
    sortedEvents() {
      if (!this.events) return [];
      
      const sorted = [...this.events].sort((a, b) => {
        const dateA = new Date(a.event_ts).getTime();
        const dateB = new Date(b.event_ts).getTime();
        return dateB - dateA; 
      });
      if (this.showTargetsOnly && this.targetEvents.length) {
        return sorted.filter(ev => this.isTargetEvent(ev));
      }
      return sorted;
    },
    processedEvents() {
      const events = this.sortedEvents || [];
      let lastTargetTimestamp = null;
      return events.map(ev => {
        let timeString = '';
        if (this.isTargetEvent(ev)) {
          const currentTs = this.parseTimestamp(ev.event_ts);
          if (lastTargetTimestamp != null && currentTs != null) {
            const diff = Math.abs(lastTargetTimestamp - currentTs);
            timeString = this.formatDuration(diff);
          }
          if (currentTs != null) {
            lastTargetTimestamp = currentTs;
          }
        }
        return { ...ev, time: timeString };
      });
    },
    targetEventsSpan() {
      const targets = (this.sortedEvents || []).filter(ev => this.isTargetEvent(ev));
      if (targets.length < 2) return '-';
      const timestamps = targets
        .map(ev => this.parseTimestamp(ev.event_ts))
        .filter(ts => ts != null)
        .sort((a, b) => a - b);
      if (timestamps.length < 2) return '-';
      const diff = Math.abs(timestamps[timestamps.length - 1] - timestamps[0]);
      return this.formatDuration(diff);
    }
  },
  methods: {
    getRowClass(item) {
      return this.isTargetEvent(item) ? 'row-target' : '';
    },
    getEventType(item) {
      // Prefer explicit name; fallback to event_data.type if present
      const name = (item && item.event_name) ? String(item.event_name) : '';
      if (name) return name;
      try {
        const parsed = typeof item.event_data === 'string' ? JSON.parse(item.event_data) : item.event_data;
        return (parsed && parsed.type) ? String(parsed.type) : '';
      } catch (e) {
        return '';
      }
    },
    isTargetEvent(item) {
      const type = this.getEventType(item).toLowerCase();
      return !!type && this.targetEvents.includes(type);
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
          }
        });
    },
    formatEventData(data) {
      try {
        if (typeof data === 'object') {
          return JSON.stringify(data, null, 2);
        }
        return data;
      } catch (error) {
        return data;
      }
    },
    formatDate(dateString) {
      try {
        const date = new Date(dateString);
        return date.toLocaleString();
      } catch (error) {
        return dateString;
      }
    },
    parseTimestamp(value) {
      if (value == null) return null;
      if (typeof value === 'number') {
        return Number.isFinite(value) ? value : null;
      }
      const str = String(value).trim();
      if (/^\d+$/.test(str)) {
        const num = parseInt(str, 10);
        // Heuristic: treat < 1e12 as seconds, otherwise ms
        return num < 1e12 ? num * 1000 : num;
      }
      // Normalize common custom formats
      const candidates = [
        str.replace('_', 'T'),
        str.replace('_', ' '),
        str
      ];
      for (const cand of candidates) {
        const t = new Date(cand).getTime();
        if (!Number.isNaN(t)) return t;
      }
      return null;
    },
    formatDuration(milliseconds) {
      if (milliseconds == null || !Number.isFinite(milliseconds)) return '';
      const totalSeconds = Math.max(0, Math.floor(milliseconds / 1000));
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;
      const parts = [];
      if (hours > 0) parts.push(`${hours}h`);
      if (minutes > 0) parts.push(`${minutes}m`);
      if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
      return parts.join(' ');
    },
    async fetchEvents() {
      try {
        await this.$store.dispatch(GET_EVENTS, {
          trackId: this.$route.params.track_id
        });
      } catch (error) {
        console.error('Failed to fetch events:', error);
      }
    }
  },
  created() {
    this.fetchEvents();
    this.refreshInterval = setInterval(this.fetchEvents, 1000);
  },
  mounted() {
    if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
      this.getTrackConfig();
    }
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }
};
</script>

<style scoped>
.event-log {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-title {
  margin: 0;
}

.event-log-card {
  margin-top: 20px;
}

.target-type {
  font-weight: 700;
  color: #3b3bd8;
}

.row-target {
  background: #f6f7ff;
}
</style>