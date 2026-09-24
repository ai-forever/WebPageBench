import { createRouter, createWebHistory } from 'vue-router';
import { createBenchRoutes, createBenchLegacyAliases } from './benchRoutes';
import { setupBenchNavigationGuard } from '@/common/benchNavigation';

import HomeView from '../views/HomeView.vue';
import StartView from '../views/StartView.vue';
import StateSelectorView from '../views/StateSelectorView.vue';
import TrackNotFoundView from '../views/TrackNotFoundView.vue';
import StateNotFoundView from '../views/StateNotFoundView.vue';
import EventLogView from '../views/EventLogView.vue';
import ChecksView from '../views/ChecksView.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/track_not_found', name: 'track_not_found', component: TrackNotFoundView },
    { path: '/state_not_found', name: 'state_not_found', component: StateNotFoundView },
    { path: '/:track_id/events', name: 'event_log', component: EventLogView },
    { path: '/:track_id/checks', name: 'condition_checks', component: ChecksView },
    ...createBenchRoutes(),
    ...createBenchLegacyAliases(),
    { path: '/:track_id/:state_id', name: 'state_selector', component: StateSelectorView },
    { path: '/:track_id', name: 'start', component: StartView },
  ],
});

setupBenchNavigationGuard(router);

export default router;
