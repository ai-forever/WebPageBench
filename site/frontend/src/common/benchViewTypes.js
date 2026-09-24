/**
 * Обезличенные имена маршрутов (view_type) единого бенчмарка.
 * Публичные имена — bench_*; bench_main остаётся алиасом хаба.
 */

export function legacyToBenchViewType(name) {
  if (!name || typeof name !== 'string') return name;
  if (name === 'bench_main') return 'bench_hub';
  return name;
}

export function benchToLegacyViewType(name) {
  if (!name || typeof name !== 'string') return name;
  if (name === 'bench_hub') return 'bench_main';
  return name;
}

const LEGACY_TO_BENCH = { bench_main: 'bench_hub' };
const BENCH_TO_LEGACY = { bench_hub: 'bench_main' };

export { LEGACY_TO_BENCH, BENCH_TO_LEGACY };

export function remapConfigViewTypes(value) {
  if (Array.isArray(value)) {
    return value.map(remapConfigViewTypes);
  }
  if (value && typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      if ((k === 'view_type' || k === 'to_view_type') && typeof v === 'string') {
        out[k] = legacyToBenchViewType(v);
      } else {
        out[k] = remapConfigViewTypes(v);
      }
    }
    return out;
  }
  return value;
}

export function remapConditionParameters(params) {
  if (!params || typeof params !== 'object') return params;
  const out = { ...params };
  if (typeof out.new_state === 'string') {
    out.new_state = legacyToBenchViewType(out.new_state);
  }
  return out;
}
