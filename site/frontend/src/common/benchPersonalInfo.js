/**
 * Unified personal information for bench profile / account pages.
 * Source priority: test_data.personal_info → test_data.user_data → state profile content.
 */

/** Personal identity fields stored only in test_data.personal_info for unified bench. */
export const PERSONAL_IDENTITY_KEYS = new Set([
  'name',
  'surname',
  'patronymic',
  'email',
  'phone',
  'address',
  'fullName',
  'full_name',
  'user_name',
]);

function asObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

function firstUserRecord(raw) {
  if (Array.isArray(raw)) {
    return raw[0] || {};
  }
  return asObject(raw) || {};
}

function splitFullName(fullName) {
  const parts = String(fullName || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length >= 3) {
    return {
      surname: parts[0],
      name: parts[1],
      patronymic: parts.slice(2).join(' '),
    };
  }
  if (parts.length === 2) {
    return { surname: parts[0], name: parts[1], patronymic: '' };
  }
  if (parts.length === 1) {
    return { surname: '', name: parts[0], patronymic: '' };
  }
  return { surname: '', name: '', patronymic: '' };
}

function buildFullName({ surname, name, patronymic, fullName, full_name, user_name }) {
  if (fullName) return String(fullName).trim();
  if (full_name) return String(full_name).trim();
  if (user_name) return String(user_name).trim();
  const parts = [surname, name, patronymic].filter(Boolean);
  if (parts.length) return parts.join(' ');
  return '';
}

function buildShortName({ surname, name, fullName }) {
  const fio = fullName || buildFullName({ surname, name });
  if (!fio) return 'Пользователь';
  const parts = fio.trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[1]} ${parts[0][0]}.`;
  }
  return parts[0];
}

function readStateProfileUserData(trackConfig) {
  if (!trackConfig) return null;
  const fromAlias = trackConfig.state_profile?.content?.user_data;
  if (asObject(fromAlias)) return fromAlias;

  for (const key of Object.keys(trackConfig)) {
    if (!key.startsWith('state_') || key === 'state_hub') continue;
    const userData = trackConfig[key]?.content?.user_data;
    if (asObject(userData)) return userData;
  }
  return null;
}

function normalizeRaw(raw, { loginFallback = false, loginData = {} } = {}) {
  const source = asObject(raw) || {};
  let surname = source.surname || '';
  let name = source.name || '';
  let patronymic = source.patronymic || '';

  if (!surname && !patronymic && source.name && String(source.name).includes(' ')) {
    const split = splitFullName(source.name);
    surname = split.surname;
    name = split.name;
    patronymic = split.patronymic;
  }

  const fullName = buildFullName({ ...source, surname, name, patronymic });
  const email = source.email || (loginFallback ? (loginData.email || loginData.login || '') : '');
  const phone = source.phone || (loginFallback ? (loginData.phone || '') : '');
  const address = source.address || '';

  return {
    surname,
    name,
    patronymic,
    fullName: fullName || 'Пользователь',
    email,
    phone,
    address,
    shortName: buildShortName({ surname, name, fullName }),
  };
}

/** @returns {ReturnType<typeof normalizeRaw>} */
export function getBenchPersonalInfo(trackConfig) {
  const testData = (trackConfig && trackConfig.test_data) || {};
  const loginData = testData.login_data || {};

  const personalInfo = asObject(testData.personal_info);
  if (personalInfo) {
    return normalizeRaw(personalInfo);
  }

  const fromUserData = firstUserRecord(testData.user_data);
  if (Object.keys(fromUserData).length) {
    return normalizeRaw(fromUserData, { loginFallback: true, loginData });
  }

  const fromState = readStateProfileUserData(trackConfig);
  if (fromState) {
    return normalizeRaw(fromState, { loginFallback: true, loginData });
  }

  return normalizeRaw({}, { loginFallback: true, loginData });
}

export function getBenchLoginData(trackConfig) {
  return ((trackConfig && trackConfig.test_data && trackConfig.test_data.login_data) || {});
}

function stripPersonalIdentityFields(raw) {
  const source = asObject(raw) || {};
  const extras = { ...source };
  PERSONAL_IDENTITY_KEYS.forEach((key) => {
    delete extras[key];
  });
  return extras;
}

export function getDomainUserExtras(trackConfig) {
  const raw = (trackConfig && trackConfig.test_data && trackConfig.test_data.user_data) || {};
  if (Array.isArray(raw)) {
    return stripPersonalIdentityFields(raw[0] || {});
  }
  return stripPersonalIdentityFields(raw);
}

export function getShopUserContext(trackConfig) {
  const personal = getBenchPersonalInfo(trackConfig);
  const extras = getDomainUserExtras(trackConfig);
  return {
    ...extras,
    surname: personal.surname,
    name: personal.name,
    patronymic: personal.patronymic,
    email: personal.email,
    phone: personal.phone,
    address: personal.address,
    fullName: personal.fullName,
    shortName: personal.shortName,
  };
}

function buildRailPassengerRecord(personal, extras = {}) {
  const cleanExtras = stripPersonalIdentityFields(extras);
  return {
    ...cleanExtras,
    name: personal.fullName,
    email: personal.email,
    phone: personal.phone,
    surname: personal.surname,
    firstName: personal.name,
    patronymic: personal.patronymic,
  };
}

export function getRailPassengers(trackConfig) {
  const personal = getBenchPersonalInfo(trackConfig);
  const raw = (trackConfig && trackConfig.test_data && trackConfig.test_data.user_data) || [];
  const list = Array.isArray(raw) ? raw : (raw ? [raw] : []);
  const passengers = [buildRailPassengerRecord(personal, list[0] || {})];
  if (list.length > 1) {
    passengers.push(...list.slice(1));
  }
  return passengers;
}

export function getRailPrimaryPassenger(trackConfig) {
  return getRailPassengers(trackConfig)[0] || buildRailPassengerRecord(getBenchPersonalInfo(trackConfig));
}

export function getBenchProfileRoute(domain) {
  const routes = {
    shop: { name: 'bench_catalog_profile', stateId: 'state_profile' },
    books: { name: 'bench_books_profile', stateId: 'state_profile' },
    grocery: { name: 'bench_grocery_profile', stateId: 'state_profile' },
    rail: { name: 'bench_rail_profile', stateId: 'state_profile' },
    files: { name: 'bench_files_cabinet', stateId: 'state_files_main' },
  };
  return routes[domain] || null;
}

/** Stable session key for basket/auth storage in unified bench. */
export function getBenchSessionUser(trackConfig) {
  const loginData = getBenchLoginData(trackConfig);
  return loginData.login || 'guest';
}

/**
 * Grocery display + checkout context: unified personal fields merged with
 * domain-specific extras (bonus_points, card_number, address_details, …).
 */
export function getGroceryUserContext(trackConfig) {
  const personal = getBenchPersonalInfo(trackConfig);
  const extras = getDomainUserExtras(trackConfig);
  return {
    ...extras,
    name: personal.name,
    surname: personal.surname,
    patronymic: personal.patronymic,
    email: personal.email,
    phone: personal.phone,
    address: personal.address,
    fullName: personal.fullName,
    shortName: personal.shortName,
  };
}
