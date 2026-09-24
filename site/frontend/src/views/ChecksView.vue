<template>
  <div class="condition-checks">
    <div class="page-header">
      <h1 class="page-title">{{ testName || 'Condition Checks' }}</h1>
    </div>
    <v-card class="checks-card" elevation="2">
      <v-card-title>
        Track: {{ $route.params.track_id }}
      </v-card-title>
      <v-card-subtitle>
        {{ passedCount }} / {{ totalConditionsEffective }} conditions passed
        <span v-if="totalConditionsEffective > 0" :class="allPassed ? 'status-passed' : 'status-pending'">
          {{ allPassed ? '(All Passed ✅)' : '(In Progress ⏳)' }}
        </span>
        <br v-if="totalTimeDisplay" />
        <span v-if="totalTimeDisplay" class="total-time">
          ⏱️ Total time: {{ totalTimeDisplay }}
        </span>
      </v-card-subtitle>

      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="conditionResults"
          :items-per-page="-1"
          class="elevation-0"
          :item-class="getRowClass"
        >
          <template v-slot:[`item.status`]="{ item }">
            <div class="status-cell">
              <span v-if="item.group" class="group-indicator" :class="item.group_success ? 'group-passed' : 'group-pending'">
                {{ item.group_success ? '✅' : '⏳' }}
              </span>
              <span v-else class="status-icon">{{ item.status ? '✅' : '⏳' }}</span>
              <span v-if="item.group && item.status" class="individual-status">✓</span>
            </div>
          </template>
          <template v-slot:[`item.description`]="{ item }">
            <div>
              <span v-if="item.group" class="group-badge" :class="item.group_success ? 'group-badge-passed' : 'group-badge-pending'">
                OR: {{ item.group }}
              </span>
              <span :class="{ 'text-muted': !item.description }">
                {{ item.description || '-' }}
              </span>
            </div>
          </template>
          <template v-slot:[`item.event_name`]="{ item }">
            <span class="event-name">{{ item.event_name }}</span>
          </template>
          <template v-slot:[`item.parameters`]="{ item }">
            <pre class="parameters-pre">{{ formatParameters(item.parameters) }}</pre>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import { GET_EVENTS, GET_TRACK_CONFIG } from "@/store/actions.type";

export default {
  name: 'ChecksView',
  data() {
    return {
      headers: [
        { title: 'Status', key: 'status', sortable: false, width: '80px' },
        { title: 'Description', key: 'description', sortable: false },
        { title: 'Event Type', key: 'event_name', sortable: false },
        { title: 'Parameters', key: 'parameters', sortable: false }
      ],
      refreshInterval: null
    };
  },
  computed: {
    ...mapGetters(['events', 'trackConfig']),
    testName() {
      return (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.test_name) || '';
    },
    conditions() {
      return (this.trackConfig && this.trackConfig.test_data && this.trackConfig.test_data.conditions) || [];
    },
    totalConditions() {
      return this.conditions.length;
    },
    conditionResults() {
      if (!this.conditions || !this.events) return [];

      // First pass: check each condition individually
      const results = this.conditions.map((condition, index) => {
        const eventName = condition.event_name;
        const parameters = condition.parameters || {};
        const description = condition.description || '';
        const group = condition.group || null;

        return {
          id: index + 1,
          status: !!this.findMatchingEvent(condition),
          description: description,
          event_name: eventName,
          parameters: parameters,
          group: group,
          group_success: null
        };
      });

      // Second pass: calculate group success (OR logic)
      const groups = {};
      for (let i = 0; i < results.length; i++) {
        const group = results[i].group;
        if (group) {
          if (!groups[group]) {
            groups[group] = [];
          }
          groups[group].push(i);
        }
      }

      const groupSuccess = {};
      for (const [group, indices] of Object.entries(groups)) {
        groupSuccess[group] = indices.some(i => results[i].status);
      }

      // Set group_success on each grouped condition
      for (let i = 0; i < results.length; i++) {
        const group = results[i].group;
        if (group) {
          results[i].group_success = groupSuccess[group];
        }
      }

      return results;
    },
    passedCount() {
      // Count ungrouped conditions that passed + groups that passed (each group counts as 1)
      const results = this.conditionResults;
      let count = 0;
      const countedGroups = new Set();

      for (const r of results) {
        if (r.group) {
          if (!countedGroups.has(r.group) && r.group_success) {
            count++;
            countedGroups.add(r.group);
          }
        } else if (r.status) {
          count++;
        }
      }
      return count;
    },
    totalConditionsEffective() {
      // Count ungrouped conditions + number of unique groups
      const results = this.conditionResults;
      const groups = new Set();
      let ungroupedCount = 0;

      for (const r of results) {
        if (r.group) {
          groups.add(r.group);
        } else {
          ungroupedCount++;
        }
      }
      return ungroupedCount + groups.size;
    },
    allPassed() {
      return this.totalConditionsEffective > 0 && this.passedCount === this.totalConditionsEffective;
    },
    passedConditionEvents() {
      if (!this.conditions || !this.events) return [];

      const matchedEvents = [];
      const matchedGroups = new Set();

      for (const condition of this.conditions) {
        const group = condition.group;

        // Skip if this group already has a matched event
        if (group && matchedGroups.has(group)) {
          continue;
        }

        const matched = this.findMatchingEvent(condition);
        if (matched) {
          matchedEvents.push(matched);
          if (group) {
            matchedGroups.add(group);
          }
        }
      }

      return matchedEvents;
    },
    totalTimeDisplay() {
      if (!this.events || this.events.length === 0) return '';
      if (this.passedConditionEvents.length === 0) return '';
      
      const allTimestamps = this.events
        .map(e => this.parseTimestamp(e.event_ts))
        .filter(ts => ts != null);
      
      if (allTimestamps.length === 0) return '';
      
      const firstTimestamp = Math.min(...allTimestamps);
      const passedTimestamps = this.passedConditionEvents
        .map(e => this.parseTimestamp(e.event_ts))
        .filter(ts => ts != null);
      
      if (passedTimestamps.length === 0) return '';

      const lastPassedTimestamp = Math.max(...passedTimestamps);
      const durationMs = lastPassedTimestamp - firstTimestamp;
      
      if (durationMs < 0) return '';
      
      return this.formatDuration(durationMs);
    }
  },
  methods: {
    parseEventData(event) {
      let eventData = event && event.event_data;
      if (typeof eventData === 'string') {
        try {
          eventData = JSON.parse(eventData);
        } catch (e) {
          return {};
        }
      }
      return eventData && typeof eventData === 'object' ? eventData : {};
    },
    paramSpec(paramValue) {
      if (
        paramValue &&
        typeof paramValue === 'object' &&
        !Array.isArray(paramValue) &&
        Object.prototype.hasOwnProperty.call(paramValue, 'value')
      ) {
        return { expected: paramValue.value, op: paramValue.condition || 'equal' };
      }
      return { expected: paramValue, op: 'equal' };
    },
    usesLastQuantityMatch(condition) {
      const matchMode = condition && condition.match;
      if (matchMode === 'any') return false;
      if (matchMode === 'last') return true;
      const eventName = condition && condition.event_name;
      const parameters = (condition && condition.parameters) || {};
      if (eventName === 'basket_add' || eventName === 'basket_remove') {
        return Object.prototype.hasOwnProperty.call(parameters, 'amount');
      }
      if (eventName === 'select_seat') {
        return Object.prototype.hasOwnProperty.call(parameters, 'seats_amount');
      }
      if (eventName === 'bench_hotel_select_guests') {
        return (
          Object.prototype.hasOwnProperty.call(parameters, 'guestsCount') ||
          Object.prototype.hasOwnProperty.call(parameters, 'roomsCount')
        );
      }
      return false;
    },
    quantityEventFamily(eventName) {
      if (eventName === 'basket_add' || eventName === 'basket_remove') {
        return ['basket_add', 'basket_remove'];
      }
      return [eventName];
    },
    identityItemId(parameters) {
      if (!parameters || !Object.prototype.hasOwnProperty.call(parameters, 'item_id')) {
        return undefined;
      }
      const spec = this.paramSpec(parameters.item_id);
      return spec.op === 'equal' ? spec.expected : undefined;
    },
    findMatchingEvent(condition) {
      const eventName = condition.event_name;
      const parameters = condition.parameters || {};
      const events = this.events || [];

      if (this.usesLastQuantityMatch(condition)) {
        const family = this.quantityEventFamily(eventName);
        const itemId =
          eventName === 'basket_add' || eventName === 'basket_remove'
            ? this.identityItemId(parameters)
            : undefined;
        let last = null;
        for (const event of events) {
          if (!family.includes(event.event_name)) continue;
          const eventData = this.parseEventData(event);
          if (itemId !== undefined && eventData.item_id !== itemId) continue;
          last = event;
        }
        if (!last) return null;
        return this.conditionMatchesEventData(parameters, this.parseEventData(last)) ? last : null;
      }

      for (const event of events) {
        if (event.event_name !== eventName) continue;
        const eventData = this.parseEventData(event);
        if (this.conditionMatchesEventData(parameters, eventData)) {
          return event;
        }
      }
      return null;
    },
    toNumber(value) {
      if (typeof value === 'number') return Number.isFinite(value) ? value : null;
      if (typeof value === 'string') {
        const trimmed = value.trim();
        if (trimmed === '') return null;
        const num = Number(trimmed);
        return Number.isFinite(num) ? num : null;
      }
      return null;
    },
    matchesWildcard(actual, pattern) {
      // Split on * wildcards, escape each literal piece, rejoin with .*
      const parts = pattern.split('*').map(p => p.replace(/[.+^${}()|[\]\\]/g, '\\$&'));
      const regex = new RegExp('^' + parts.join('.*') + '$');
      return regex.test(String(actual));
    },
    compare(actual, expected, op) {
      if (!op || op === 'equal') {
        if (typeof expected === 'string' && expected.includes('*')) {
          return this.matchesWildcard(actual, expected);
        }
        return actual === expected;
      }
      const a = this.toNumber(actual);
      const b = this.toNumber(expected);
      if (a == null || b == null) return false;

      if (op === 'greater_than') return a > b;
      if (op === 'greater_than_or_equal') return a >= b;
      if (op === 'less_than') return a < b;
      if (op === 'less_than_or_equal') return a <= b;
      return false;
    },
    conditionMatchesEventData(parameters, eventData) {
      if (!parameters || Object.keys(parameters).length === 0) return true;

      for (const [paramKey, paramValue] of Object.entries(parameters)) {
        // Per-parameter format:
        // "amount": { "value": 3, "condition": "greater_than" }
        // Scalar values use equality.
        let expectedValue = paramValue;
        let op = 'equal';

        if (
          paramValue &&
          typeof paramValue === 'object' &&
          !Array.isArray(paramValue) &&
          Object.prototype.hasOwnProperty.call(paramValue, 'value')
        ) {
          expectedValue = paramValue.value;
          op = paramValue.condition || 'equal';
        }

        if (!this.compare(eventData[paramKey], expectedValue, op)) {
          return false;
        }
      }

      return true;
    },
    getRowClass(item) {
      if (item.group) {
        return item.group_success ? 'row-group-passed' : 'row-group-pending';
      }
      return item.status ? 'row-passed' : 'row-pending';
    },
    formatParameters(params) {
      if (!params || Object.keys(params).length === 0) {
        return '{}';
      }
      return JSON.stringify(params, null, 2);
    },
    getTrackConfig() {
      this.$store
        .dispatch(GET_TRACK_CONFIG, { trackId: this.$route.params.track_id })
        .then(() => {
          if (!this.trackConfig || Object.keys(this.trackConfig).length === 0) {
            this.$router.push({ name: "not_found" });
          }
        })
        .catch(error => {
          console.error('Failed to fetch track config:', error);
        });
    },
    async fetchEvents() {
      try {
        await this.$store.dispatch(GET_EVENTS, {
          trackId: this.$route.params.track_id
        });
      } catch (error) {
        console.error('Failed to fetch events:', error);
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
        return num < 1e12 ? num * 1000 : num;
      }
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
    }
  },
  created() {
    this.fetchEvents();
    this.refreshInterval = setInterval(this.fetchEvents, 2000);
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
.condition-checks {
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
  font-size: 2rem;
  font-weight: 600;
}

.checks-card {
  margin-top: 20px;
}

.status-icon {
  font-size: 1.5rem;
  display: inline-block;
}

.event-name {
  font-family: Roboto, Arial, Helvetica, sans-serif;
  font-weight: 600;
  color: #2c3e50;
}

.parameters-pre {
  font-family: Roboto, Arial, Helvetica, sans-serif;
  font-size: 0.875rem;
  margin: 0;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  overflow-x: auto;
}

.text-muted {
  color: #999;
  font-style: italic;
}

.row-passed {
  background: #f0f9f0;
}

.row-pending {
  background: #fff9e6;
}

.status-passed {
  color: #4caf50;
  font-weight: 600;
  margin-left: 8px;
}

.status-pending {
  color: #ff9800;
  font-weight: 600;
  margin-left: 8px;
}

.total-time {
  color: #1976d2;
  font-weight: 600;
  font-size: 1rem;
}

.status-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.group-indicator {
  font-size: 1.5rem;
}

.individual-status {
  font-size: 0.75rem;
  color: #4caf50;
  font-weight: bold;
}

.group-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  margin-right: 8px;
  text-transform: uppercase;
}

.group-badge-passed {
  background-color: #e8f5e9;
  color: #2e7d32;
  border: 1px solid #a5d6a7;
}

.group-badge-pending {
  background-color: #fff3e0;
  color: #e65100;
  border: 1px solid #ffcc80;
}

.row-group-passed {
  background: #e8f5e9;
}

.row-group-pending {
  background: #fff8e1;
}
</style>

