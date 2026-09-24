import store from '@/store';
import { GET_TRACK_CONFIG, GET_KV_STORE } from '@/store/actions.type';
import { PATCH_TRACK_CONFIG } from '@/store/mutations.type';
import { isUnifiedBench, mergeDomainIntoConfig } from '@/common/benchTheme';
import { legacyToBenchViewType } from '@/common/benchViewTypes';

const BENCH_ROUTE_DOMAIN_MAP = [
  ['bench_catalog_', 'shop'],
  ['bench_books_', 'books'],
  ['bench_grocery_', 'grocery'],
  ['bench_rail_', 'rail'],
  ['bench_hotel_', 'hotels'],
  ['bench_files_', 'files'],
];

function hasTrackConfig(trackConfig, loadedTrackId, routeTrackId) {
  if (!trackConfig || Object.keys(trackConfig).length === 0) {
    return false;
  }
  if (!routeTrackId) {
    return true;
  }
  return loadedTrackId === routeTrackId;
}

export function resolveBenchDomain(routeName) {
  if (!routeName || typeof routeName !== 'string') {
    return null;
  }
  const mapped = legacyToBenchViewType(routeName);
  for (const [prefix, domain] of BENCH_ROUTE_DOMAIN_MAP) {
    if (mapped.startsWith(prefix)) {
      return domain;
    }
  }
  return null;
}

/** Подмешивает domain_configs в trackConfig (нужно для state_basket и common_elements). */
export function ensureBenchDomainMerged(domain) {
  const trackConfig = store.getters.trackConfig;
  if (!domain || !isUnifiedBench(trackConfig)) {
    return trackConfig;
  }
  const merged = mergeDomainIntoConfig(trackConfig, domain);
  store.commit(PATCH_TRACK_CONFIG, merged);
  return merged;
}

export function resolveBenchStateId(stateId, trackConfig = store.getters.trackConfig) {
  if (!stateId || !trackConfig) return stateId;
  if (trackConfig[stateId]) return stateId;

  const activeDomain = trackConfig.test_data?.active_bench_domain;
  const domains = activeDomain
    ? [activeDomain]
    : Object.keys(trackConfig.domain_configs || {});

  for (const domainKey of domains) {
    const aliases = trackConfig.domain_configs?.[domainKey]?.state_aliases;
    if (!aliases || !aliases[stateId]) continue;
    const canonical = aliases[stateId];
    if (trackConfig[canonical]) return canonical;
  }
  return stateId;
}

function isNavigationFailure(err) {
  if (!err) return false;
  const name = err.name || '';
  return name === 'NavigationDuplicated' || name === 'NavigationCancelled';
}

const DOMAIN_BASKET_SPEC = {
  shop: {
    canonicalState: 'state_shop_basket',
    defaultView: 'bench_catalog_basket',
  },
  books: {
    canonicalState: 'state_books_basket',
    defaultView: 'bench_books_basket',
  },
  grocery: {
    canonicalState: 'state_grocery_basket',
    defaultView: 'bench_grocery_basket',
  },
};

/** Навигация в корзину домена (shop | books). */
export function navigateToDomainBasket(domain, router, trackId) {
  const spec = DOMAIN_BASKET_SPEC[domain];
  if (!spec) return Promise.resolve(false);

  ensureBenchDomainMerged(domain);
  const cfg = store.getters.trackConfig;
  const tid = trackId || router.currentRoute.value?.params?.track_id;
  if (!tid) return Promise.resolve(false);

  const legacyState = 'state_basket';
  const stateKey =
    (cfg && cfg[spec.canonicalState] && spec.canonicalState)
    || (cfg && cfg[legacyState] && legacyState)
    || spec.canonicalState;
  const stateDef = cfg && cfg[stateKey];
  const routeName = legacyToBenchViewType(
    (stateDef && stateDef.view_type) || spec.defaultView,
  );
  if (!stateDef) {
    console.warn('[bench] Basket state missing in config:', domain, stateKey);
    return Promise.resolve(false);
  }

  const location = {
    name: routeName,
    params: { track_id: tid, state_id: stateKey },
  };
  const path = `/${tid}/${stateKey}/${routeName}`;

  return router.push(location).catch((err) => {
    if (isNavigationFailure(err)) return true;
    return router.push({ path }).catch((err2) => {
      if (isNavigationFailure(err2)) return true;
      console.warn('[bench] Basket navigation failed:', domain, location, err, err2);
      return false;
    });
  });
}

/** Навигация в корзину «Книги». */
export function navigateToBooksBasket(router, trackId) {
  return navigateToDomainBasket('books', router, trackId);
}

/** Навигация в корзину «Маркет». */
export function navigateToShopBasket(router, trackId) {
  return navigateToDomainBasket('shop', router, trackId);
}

/** Навигация в корзину «Продукты». */
export function navigateToGroceryBasket(router, trackId) {
  return navigateToDomainBasket('grocery', router, trackId);
}

/** Навигация с учётом legacy-имён маршрутов и state_aliases unified bench. */
export function pushBenchRoute(router, { name, stateId, trackId, query, hash }) {
  if (!name && !stateId) {
    return Promise.resolve(false);
  }

  const routeName = name ? legacyToBenchViewType(name) : null;
  const domain = routeName ? resolveBenchDomain(routeName) : null;
  if (domain) {
    ensureBenchDomainMerged(domain);
  }

  if (routeName === 'bench_books_basket') {
    return navigateToBooksBasket(router, trackId);
  }
  if (routeName === 'bench_catalog_basket') {
    return navigateToShopBasket(router, trackId);
  }
  if (routeName === 'bench_grocery_basket') {
    return navigateToGroceryBasket(router, trackId);
  }

  const cfg = store.getters.trackConfig;
  const resolvedState = resolveBenchStateId(stateId, cfg);
  const tid = trackId || router.currentRoute.value?.params?.track_id;
  if (!tid || !resolvedState || !routeName) {
    return Promise.resolve(false);
  }

  const location = {
    name: routeName,
    params: { track_id: tid, state_id: resolvedState },
    query,
    hash,
  };
  const path = `/${tid}/${resolvedState}/${routeName}`;
  return router.push(location).catch((err) => {
    if (isNavigationFailure(err)) return true;
    return router.push({ path, query, hash }).catch((err2) => {
      if (isNavigationFailure(err2)) return true;
      console.warn('[bench] Navigation failed:', location, err, err2);
      return false;
    });
  });
}

/**
 * При unified_bench перенаправляет алиас bench_main → bench_hub.
 */
export function setupBenchNavigationGuard(router) {
  router.beforeEach(async (to, from, next) => {
    const trackId = to.params?.track_id;
    let trackConfig = store.getters.trackConfig;
    let currentTrackId = store.getters.currentTrackId;

    if (trackId && !hasTrackConfig(trackConfig, currentTrackId, trackId)) {
      try {
        await store.dispatch(GET_TRACK_CONFIG, { trackId });
        trackConfig = store.getters.trackConfig;
        currentTrackId = store.getters.currentTrackId;
      } catch (e) {
        return next({ name: 'track_not_found' });
      }
    }

    if (!isUnifiedBench(trackConfig)) {
      return next();
    }

    const mapped = legacyToBenchViewType(to.name);
    const targetRouteName = mapped || to.name;
    const benchDomain = resolveBenchDomain(targetRouteName);
    if (benchDomain && isUnifiedBench(trackConfig)) {
      const prevDomain = trackConfig?.test_data?.active_bench_domain;
      trackConfig = mergeDomainIntoConfig(trackConfig, benchDomain);
      store.commit(PATCH_TRACK_CONFIG, trackConfig);
      const kvPath = trackConfig?.test_data?.kv_store_path;
      const kv = store.getters.kvStore;
      const kvEmpty = !kv || typeof kv !== 'object' || !Object.keys(kv).length;
      if (kvPath && (kvEmpty || prevDomain !== benchDomain)) {
        try {
          await store.dispatch(GET_KV_STORE, { kvPath });
        } catch (e) {
          console.warn('[bench] KV load failed', kvPath, e);
        }
      }
    }

    if (mapped && mapped !== to.name) {
      return next({
        name: mapped,
        params: to.params,
        query: to.query,
        hash: to.hash,
      });
    }
    return next();
  });
}
