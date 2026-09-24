import { computed } from 'vue';
import store from '@/store';
import { UI_VARIANT_DEFAULTS } from './constants';

/**
 * Resolve UI widget variant from merged trackConfig.
 * Priority: domain_configs[domain].ui_variants > test_data.ui_variants > top-level ui_variants > default.
 */
export function resolveUiVariant(trackConfig, elementType, domain = null) {
  const activeDomain =
    domain ||
    trackConfig?.test_data?.active_bench_domain ||
    trackConfig?.test_data?.bench_first_domain ||
    null;

  const domainVariants =
    activeDomain && trackConfig?.domain_configs?.[activeDomain]?.ui_variants;
  if (domainVariants?.[elementType]) {
    return domainVariants[elementType];
  }

  const testVariants = trackConfig?.test_data?.ui_variants;
  if (testVariants?.[elementType]) {
    return testVariants[elementType];
  }

  const globalVariants = trackConfig?.ui_variants;
  if (globalVariants?.[elementType]) {
    return globalVariants[elementType];
  }

  return UI_VARIANT_DEFAULTS[elementType] || 'standard';
}

export function useBenchUiVariant(elementType, domain = null) {
  const variant = computed(() => {
    const trackConfig = store.getters.trackConfig || {};
    return resolveUiVariant(trackConfig, elementType, domain);
  });

  return { variant };
}

export function useBenchUiVariants(domain = null) {
  const trackConfig = computed(() => store.getters.trackConfig || {});

  function get(elementType) {
    return resolveUiVariant(trackConfig.value, elementType, domain);
  }

  return { get, trackConfig };
}
