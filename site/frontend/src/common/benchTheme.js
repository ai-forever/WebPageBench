import { remapConfigViewTypes } from '@/common/benchViewTypes';

export function isUnifiedBench(trackConfig) {
  return Boolean(trackConfig?.test_data?.unified_bench);
}

export function isBenchAnonymized(trackConfig) {
  return Boolean(trackConfig?.test_data?.bench_anonymized || trackConfig?.test_data?.unified_bench);
}

export function applyBenchDocumentClass(enabled) {
  const root = document.documentElement;
  if (enabled) {
    root.classList.add('bench-anonymized');
  } else {
    root.classList.remove('bench-anonymized');
  }
}

export function resolveBenchTheme(trackConfig) {
  const testVariants = trackConfig?.test_data?.ui_variants || {};
  const globalVariants = trackConfig?.ui_variants || {};
  return testVariants.theme || globalVariants.theme || 'light';
}

export function applyBenchTheme(trackConfig) {
  applyBenchDocumentClass(isBenchAnonymized(trackConfig));
  const root = document.documentElement;
  const theme = resolveBenchTheme(trackConfig);
  if (theme && theme !== 'light') {
    root.setAttribute('data-bench-theme', theme);
  } else {
    root.removeAttribute('data-bench-theme');
  }
}

export function getBenchSections(trackConfig) {
  const sections = trackConfig?.bench_sections;
  if (Array.isArray(sections) && sections.length) {
    return sections;
  }
  return [
    { id: 'hub', label: 'Главная', state: 'state_hub', view_type: 'bench_hub', domain: null },
    { id: 'shop', label: 'Маркет', state: 'state_shop_main', view_type: 'bench_catalog_main', domain: 'shop' },
    { id: 'books', label: 'Книги', state: 'state_books_main', view_type: 'bench_books_main', domain: 'books' },
    { id: 'grocery', label: 'Продукты', state: 'state_grocery_main', view_type: 'bench_grocery_main', domain: 'grocery' },
    { id: 'rail', label: 'Поезда', state: 'state_rail_main', view_type: 'bench_rail_main', domain: 'rail' },
    { id: 'hotels', label: 'Отели', state: 'state_hotels_main', view_type: 'bench_hotel_main', domain: 'hotels' },
    { id: 'files', label: 'Файлы', state: 'state_files_main', view_type: 'bench_files_cabinet', domain: 'files' },
  ];
}


function applyDomainStateAliases(merged, domainKey) {
  const domain = merged.domain_configs?.[domainKey];
  const aliases = domain?.state_aliases;
  if (!aliases || typeof aliases !== 'object') {
    return;
  }
  Object.entries(aliases).forEach(([legacyId, canonicalId]) => {
    if (merged[canonicalId] && !merged[legacyId]) {
      merged[legacyId] = merged[canonicalId];
    }
  });
}

export function mergeDomainIntoConfig(trackConfig, domainKey) {
  const domains = trackConfig?.domain_configs;
  if (!domains || !domainKey || !domains[domainKey]) {
    return trackConfig;
  }
  const slice = remapConfigViewTypes(domains[domainKey]);
  const merged = remapConfigViewTypes({ ...trackConfig });
  if (slice.common_elements) {
    merged.common_elements = { ...slice.common_elements };
  }
  if (slice.ui_variants) {
    merged.ui_variants = { ...merged.ui_variants, ...slice.ui_variants };
    merged.test_data = merged.test_data || {};
    merged.test_data.ui_variants = {
      ...merged.test_data.ui_variants,
      ...slice.ui_variants,
    };
  }
  if (slice.test_data) {
    const preservedPersonalInfo = merged.test_data?.personal_info;
    const preservedLoginData = merged.test_data?.login_data;
    merged.test_data = { ...merged.test_data, ...slice.test_data };
    if (preservedPersonalInfo && !slice.test_data.personal_info) {
      merged.test_data.personal_info = preservedPersonalInfo;
    }
    if (preservedLoginData) {
      merged.test_data.login_data = preservedLoginData;
    }
  }
  Object.keys(slice).forEach((key) => {
    if (key.startsWith('state_')) {
      merged[key] = slice[key];
    }
  });
  merged.test_data = { ...merged.test_data, active_bench_domain: domainKey };
  applyDomainStateAliases(merged, domainKey);
  return merged;
}
