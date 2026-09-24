import { benchPageLoaders, benchRouteNames } from '@/views/bench/registry';
import { LEGACY_TO_BENCH } from '@/common/benchViewTypes';

const BENCH_PATH_OVERRIDES = {};

/**
 * Маршруты обезличенного бенчмарка (единый каталог views/bench).
 */
export function createBenchRoutes() {
  return benchRouteNames.map((name) => ({
    path: BENCH_PATH_OVERRIDES[name] || `/:track_id/:state_id/${name}`,
    name,
    component: benchPageLoaders[name],
  }));
}

/** Alias bench_main → тот же компонент, что и bench_hub */
export function createBenchLegacyAliases() {
  const routes = [
    {
      path: '/:track_id/:state_id/bench_main',
      name: 'bench_main',
      component: benchPageLoaders.bench_hub,
    },
  ];

  const seen = new Set(routes.map((r) => r.name));

  for (const [legacyName, benchName] of Object.entries(LEGACY_TO_BENCH)) {
    if (seen.has(legacyName)) continue;
    const loader = benchPageLoaders[benchName];
    if (!loader) continue;
    seen.add(legacyName);
    routes.push({
      path: BENCH_PATH_OVERRIDES[benchName] || `/:track_id/:state_id/${legacyName}`,
      name: legacyName,
      component: loader,
    });
  }

  return routes;
}
