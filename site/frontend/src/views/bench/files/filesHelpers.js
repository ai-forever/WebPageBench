const STORAGE_KEY = 'bench_files_selected_collection';

export function getFilesCollections(trackConfig) {
  const domain = trackConfig?.domain_configs?.files;
  if (Array.isArray(domain?.collections) && domain.collections.length) {
    return domain.collections;
  }
  if (Array.isArray(trackConfig?.collections) && trackConfig.collections.length) {
    return trackConfig.collections;
  }
  return [];
}

export function getFilesUiVariant(trackConfig, key, fallback) {
  const variants = {
    ...(trackConfig?.domain_configs?.files?.ui_variants || {}),
    ...(trackConfig?.test_data?.ui_variants || {}),
    ...(trackConfig?.ui_variants || {}),
  };
  return variants[key] || fallback;
}

export function rememberCollection(id) {
  try {
    sessionStorage.setItem(STORAGE_KEY, String(id || ''));
  } catch (e) {
    /* ignore */
  }
}

export function recalledCollection() {
  try {
    return sessionStorage.getItem(STORAGE_KEY) || '';
  } catch (e) {
    return '';
  }
}

export function fileHref(entry) {
  if (!entry) return '#';
  if (entry.url && String(entry.url).startsWith('/mocks/')) {
    return entry.url;
  }
  const name = entry.file || '';
  return name ? `/mocks/files/${name}` : '#';
}

const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

function pad2(value) {
  return String(value).padStart(2, '0');
}

function formatRuDate(year, month, day) {
  return `${pad2(day)}.${pad2(month)}.${year}`;
}

function daysInMonth(year, month) {
  if (month === 2) {
    const leap = (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
    return leap ? 29 : 28;
  }
  return MONTH_DAYS[month - 1] || 28;
}

function hashInRange(seed, min, max) {
  let hash = 2166136261;
  const text = String(seed);
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return min + ((hash >>> 0) % (max - min + 1));
}

export function fileAddedDate(entry, selectedYear) {
  const name = String(entry?.file || '');
  const stem = name.replace(/\.[^.]+$/, '');
  const yearFallback = Number(selectedYear) || 2024;

  const full = stem.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (full) {
    return formatRuDate(Number(full[1]), Number(full[2]), Number(full[3]));
  }

  const quarter = stem.match(/(\d{4})-q([1-4])/i);
  if (quarter) {
    const year = Number(quarter[1]);
    const month = Number(quarter[2]) * 3;
    return formatRuDate(year, month, daysInMonth(year, month));
  }

  const yearMonth = stem.match(/(\d{4})-(\d{2})(?!\d)/);
  if (yearMonth) {
    const year = Number(yearMonth[1]);
    const month = Number(yearMonth[2]);
    const day = hashInRange(name, 1, daysInMonth(year, month));
    return formatRuDate(year, month, day);
  }

  const yearMatch = stem.match(/(?:^|\D)(\d{4})(?:\D|$)/);
  const year = yearMatch ? Number(yearMatch[1]) : yearFallback;
  const month = hashInRange(`${name}:month`, 1, 12);
  const day = hashInRange(`${name}:day`, 1, daysInMonth(year, month));
  return formatRuDate(year, month, day);
}

export function fileAddedLabel(entry, selectedYear) {
  return `Добавлен ${fileAddedDate(entry, selectedYear)}`;
}
