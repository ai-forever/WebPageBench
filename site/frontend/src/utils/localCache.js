const LOGIN_KEY = 'logged_in';
const BASKET_KEY = 'basket';
const SHOP_BASKET_KEY = 'bench_catalog_basket';
const SHOP_SELECTED_ITEMS_KEY = 'selected_items_shop';
const PURCHASED_KEY = 'purchased_items';
const SHOP_FAVORITES_KEY = 'favorites_shop';
const BOOKS_FAVORITES_KEY = 'favorites_books';
const CURRENT_USER_KEY = 'current_username';
const PROMPT_STORAGE_KEY = 'one_time_prompts';
const GROCERY_LOGIN_KEY = 'bench_grocery_logged_in';
const GROCERY_USER_KEY = 'bench_grocery_current_user';
const GROCERY_BASKET_KEY = 'basket_grocery';
const GROCERY_ORDERS_KEY = 'orders_grocery';
const RAIL_LOGIN_KEY = 'bench_rail_logged_in';
const RAIL_USER_KEY = 'bench_rail_current_user';
const RAIL_USER_DATA_KEY = 'bench_rail_user_data';
const RAIL_TICKETS_KEY = 'bench_rail_tickets';
const RAIL_BOOKING_SESSION_KEY = 'bench_rail_booking_session';
// Separate login for ticket/search flow (different from main page)
const RAIL_TICKET_LOGIN_KEY = 'bench_rail_ticket_logged_in';
const RAIL_TICKET_USER_KEY = 'bench_rail_ticket_current_user';
const RAIL_TICKET_USER_DATA_KEY = 'bench_rail_ticket_user_data';

import { getBenchSessionUser, getRailPassengers } from '@/common/benchPersonalInfo.js';
import { isUnifiedBench } from '@/common/benchTheme.js';

const CLIENT_STATE_KEYS = [
  LOGIN_KEY,
  BASKET_KEY,
  SHOP_BASKET_KEY,
  SHOP_SELECTED_ITEMS_KEY,
  PURCHASED_KEY,
  SHOP_FAVORITES_KEY,
  BOOKS_FAVORITES_KEY,
  CURRENT_USER_KEY,
  PROMPT_STORAGE_KEY,
  GROCERY_LOGIN_KEY,
  GROCERY_USER_KEY,
  GROCERY_BASKET_KEY,
  GROCERY_ORDERS_KEY,
  RAIL_LOGIN_KEY,
  RAIL_USER_KEY,
  RAIL_USER_DATA_KEY,
  RAIL_TICKETS_KEY,
  RAIL_BOOKING_SESSION_KEY,
  RAIL_TICKET_LOGIN_KEY,
  RAIL_TICKET_USER_KEY,
  RAIL_TICKET_USER_DATA_KEY,
];

const EXPLICIT_LOGOUT_KEY = 'bench_explicit_logout';

let currentTrackId = null;

function trackMtimeStorageKey(trackId) {
  return `bench_track_mtime:${trackId}`;
}

function scopedKey(base) {
  return currentTrackId ? `bench:${currentTrackId}:${base}` : base;
}

const LS = typeof window !== 'undefined' ? window.localStorage : {
  getItem() { return null; },
  setItem() {},
  removeItem() {},
};

function rawGet(key) {
  try {
    return LS.getItem(key);
  } catch (e) {
    return null;
  }
}

function rawSet(key, value) {
  try {
    LS.setItem(key, value);
  } catch (e) {
    /* ignore */
  }
}

function rawRemove(key) {
  try {
    LS.removeItem(key);
  } catch (e) {
    /* ignore */
  }
}

function lsGet(base) {
  const scoped = scopedKey(base);
  const val = rawGet(scoped);
  if (val != null) return val;
  if (scoped !== base) return rawGet(base);
  return null;
}

function lsSet(base, value) {
  rawSet(scopedKey(base), value);
}

function lsRemove(base) {
  rawRemove(scopedKey(base));
  if (currentTrackId) rawRemove(base);
}

export function getBenchTrackContext() {
  return currentTrackId;
}

export function isExplicitLogout() {
  return lsGet(EXPLICIT_LOGOUT_KEY) === 'true';
}

export function markExplicitLogout() {
  lsSet(EXPLICIT_LOGOUT_KEY, 'true');
}

export function clearExplicitLogout() {
  lsRemove(EXPLICIT_LOGOUT_KEY);
}

export function clearBenchClientState() {
  CLIENT_STATE_KEYS.forEach(lsRemove);
  lsRemove(EXPLICIT_LOGOUT_KEY);
}

/** Bind storage to a track. Recreated tracks (mtime change) drop leftover carts. */
export function bindBenchTrackSession(trackId, trackMtime) {
  const nextId = trackId || null;
  const prevMtime = nextId ? rawGet(trackMtimeStorageKey(nextId)) : null;
  currentTrackId = nextId;
  if (nextId && prevMtime != null && trackMtime != null && String(prevMtime) !== String(trackMtime)) {
    clearBenchClientState();
    clearExplicitLogout();
  }
  if (nextId && trackMtime != null) {
    rawSet(trackMtimeStorageKey(nextId), String(trackMtime));
  }
}

export function isLoggedIn() {
  try {
    const val = lsGet(LOGIN_KEY);
    return val === 'true';
  } catch (e) {
    return false;
  }
}

export function setLoggedIn(value) {
  try {
    lsSet(LOGIN_KEY, value ? 'true' : 'false');
    if (value) clearExplicitLogout();
    else markExplicitLogout();
  } catch (e) {
  }
}

export function clearLogin() {
  try {
    lsRemove(LOGIN_KEY);
    markExplicitLogout();
  } catch (e) {
  }
}

function readPromptObject() {
  try {
    const raw = lsGet(PROMPT_STORAGE_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writePromptObject(obj) {
  try {
    lsSet(PROMPT_STORAGE_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

function readBasketObject() {
  try {
    const raw = lsGet(BASKET_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeBasketObject(obj) {
  try {
    lsSet(BASKET_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

// МАРКЕТ basket storage (map of { itemId: quantity })
function readShopBasketObject() {
  try {
    const raw = lsGet(SHOP_BASKET_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeShopBasketObject(obj) {
  try {
    lsSet(SHOP_BASKET_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

// МАРКЕТ favorites storage (set of item keys per user)
function readShopFavoritesObject() {
  try {
    const raw = lsGet(SHOP_FAVORITES_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeShopFavoritesObject(obj) {
  try {
    lsSet(SHOP_FAVORITES_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

// МАРКЕТ selected items storage (object of selected states per user)
function readShopSelectedItemsObject() {
  try {
    const raw = lsGet(SHOP_SELECTED_ITEMS_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeShopSelectedItemsObject(obj) {
  try {
    lsSet(SHOP_SELECTED_ITEMS_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

function readPurchasedObject() {
  try {
    const raw = lsGet(PURCHASED_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writePurchasedObject(obj) {
  try {
    lsSet(PURCHASED_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

export function setCurrentUsername(username) {
  try {
    lsSet(CURRENT_USER_KEY, username || '');
  } catch (e) {
  }
}

export function getCurrentUsername() {
  try {
    return lsGet(CURRENT_USER_KEY) || '';
  } catch (e) {
    return '';
  }
}

export function hasPromptBeenSeen(key) {
  if (!key) return false;
  const obj = readPromptObject();
  return !!obj[key];
}

export function markPromptSeen(key) {
  if (!key) return;
  const obj = readPromptObject();
  obj[key] = true;
  writePromptObject(obj);
}

export function clearPromptFlag(key) {
  if (!key) return;
  const obj = readPromptObject();
  if (obj[key]) {
    delete obj[key];
    writePromptObject(obj);
  }
}

export function getBasketItems(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBasketObject();
  const arr = obj[user] || [];
  return Array.isArray(arr) ? arr : [];
}

export function addBasketItem(username, itemKey) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBasketObject();
  const arr = Array.isArray(obj[user]) ? obj[user].slice() : [];
  if (!arr.includes(itemKey)) {
    arr.push(itemKey);
    obj[user] = arr;
    writeBasketObject(obj);
  }
}

export function removeBasketItem(username, itemKey) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBasketObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  obj[user] = arr.filter(k => k !== itemKey);
  writeBasketObject(obj);
}

export function clearBasket(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBasketObject();
  if (obj[user]) {
    delete obj[user];
    writeBasketObject(obj);
  }
}

// ----- МАРКЕТ basket public helpers -----
export function getShopBasket(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopBasketObject();
  const map = obj[user] || {};
  return map && typeof map === 'object' ? map : {};
}

export function setShopBasketItem(username, itemKey, quantity) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopBasketObject();
  const map = (obj[user] && typeof obj[user] === 'object') ? { ...obj[user] } : {};
  const q = Math.max(0, Number.isFinite(quantity) ? Math.floor(quantity) : 0);
  if (q <= 0) {
    if (map[itemKey] != null) delete map[itemKey];
  } else {
    map[itemKey] = q;
  }
  obj[user] = map;
  writeShopBasketObject(obj);
}

export function addShopBasketItem(username, itemKey, quantity) {
  const cur = getShopBasket(username);
  const prev = Number(cur[itemKey] || 0);
  const add = Math.max(1, Number.isFinite(quantity) ? Math.floor(quantity) : 1);
  setShopBasketItem(username, itemKey, prev + add);
}

export function incrementShopBasketItem(username, itemKey, delta) {
  const cur = getShopBasket(username);
  const prev = Number(cur[itemKey] || 0);
  const next = prev + (Number.isFinite(delta) ? Math.floor(delta) : 1);
  setShopBasketItem(username, itemKey, Math.max(0, next));
}

export function removeShopBasketItem(username, itemKey) {
  setShopBasketItem(username, itemKey, 0);
}

export function clearShopBasket(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopBasketObject();
  if (obj[user]) {
    delete obj[user];
    writeShopBasketObject(obj);
  }
}

export function getShopBasketCount(username) {
  const map = getShopBasket(username);
  return Object.values(map).reduce((sum, q) => sum + (Number.isFinite(q) ? q : 0), 0);
}

// Merge basket items from one user into another and optionally clear the source
export function mergeShopBasket(sourceUsername, targetUsername, clearSource = true) {
  const src = sourceUsername || 'guest';
  const dst = targetUsername || getCurrentUsername() || 'guest';
  if (!dst) return;
  const obj = readShopBasketObject();
  const srcMap = (obj[src] && typeof obj[src] === 'object') ? obj[src] : {};
  const dstMap = (obj[dst] && typeof obj[dst] === 'object') ? obj[dst] : {};
  const out = { ...dstMap };
  Object.keys(srcMap).forEach(k => {
    const a = Number(dstMap[k] || 0);
    const b = Number(srcMap[k] || 0);
    const sum = Math.max(0, (Number.isFinite(a) ? a : 0) + (Number.isFinite(b) ? b : 0));
    if (sum > 0) out[k] = sum; else if (out[k] != null) delete out[k];
  });
  obj[dst] = out;
  if (clearSource && obj[src]) delete obj[src];
  writeShopBasketObject(obj);
}

// ----- МАРКЕТ favorites public helpers -----
export function getShopFavorites(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopFavoritesObject();
  const arr = obj[user] || [];
  return Array.isArray(arr) ? arr : [];
}

export function isShopFavorite(username, itemKey) {
  if (!itemKey) return false;
  const arr = getShopFavorites(username);
  return Array.isArray(arr) ? arr.includes(itemKey) : false;
}

export function addShopFavorite(username, itemKey) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopFavoritesObject();
  const arr = Array.isArray(obj[user]) ? obj[user].slice() : [];
  if (!arr.includes(itemKey)) {
    arr.push(itemKey);
    obj[user] = arr;
    writeShopFavoritesObject(obj);
  }
}

export function removeShopFavorite(username, itemKey) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopFavoritesObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  obj[user] = arr.filter(k => k !== itemKey);
  writeShopFavoritesObject(obj);
}

export function toggleShopFavorite(username, itemKey) {
  if (!itemKey) return;
  if (isShopFavorite(username, itemKey)) removeShopFavorite(username, itemKey);
  else addShopFavorite(username, itemKey);
}

export function clearShopFavorites(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopFavoritesObject();
  if (obj[user]) {
    delete obj[user];
    writeShopFavoritesObject(obj);
  }
}

export function getShopFavoritesCount(username) {
  const arr = getShopFavorites(username);
  return Array.isArray(arr) ? arr.length : 0;
}

// ----- Книги favorites storage (set of item keys per user) -----
function readBooksFavoritesObject() {
  try {
    const raw = lsGet(BOOKS_FAVORITES_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeBooksFavoritesObject(obj) {
  try {
    lsSet(BOOKS_FAVORITES_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

// Книги favorites public helpers
export function getBooksFavorites(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBooksFavoritesObject();
  const arr = obj[user] || [];
  return Array.isArray(arr) ? arr : [];
}

export function isBooksFavorite(username, itemKey) {
  if (!itemKey) return false;
  const arr = getBooksFavorites(username);
  return Array.isArray(arr) ? arr.includes(itemKey) : false;
}

export function addBooksFavorite(username, itemKey) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBooksFavoritesObject();
  const arr = Array.isArray(obj[user]) ? obj[user].slice() : [];
  if (!arr.includes(itemKey)) {
    arr.push(itemKey);
    obj[user] = arr;
    writeBooksFavoritesObject(obj);
  }
}

export function removeBooksFavorite(username, itemKey) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBooksFavoritesObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  obj[user] = arr.filter(k => k !== itemKey);
  writeBooksFavoritesObject(obj);
}

export function toggleBooksFavorite(username, itemKey) {
  if (!itemKey) return;
  if (isBooksFavorite(username, itemKey)) removeBooksFavorite(username, itemKey);
  else addBooksFavorite(username, itemKey);
}

export function clearBooksFavorites(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readBooksFavoritesObject();
  if (obj[user]) {
    delete obj[user];
    writeBooksFavoritesObject(obj);
  }
}

export function getBooksFavoritesCount(username) {
  const arr = getBooksFavorites(username);
  return Array.isArray(arr) ? arr.length : 0;
}

// ----- МАРКЕТ selected items public helpers -----
export function getShopSelectedItems(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopSelectedItemsObject();
  const userSelections = obj[user] || {};
  return typeof userSelections === 'object' ? userSelections : {};
}

export function setShopSelectedItems(username, selectedItemsObj) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopSelectedItemsObject();
  obj[user] = selectedItemsObj || {};
  writeShopSelectedItemsObject(obj);
}

export function setShopItemSelected(username, itemKey, isSelected) {
  if (!itemKey) return;
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopSelectedItemsObject();
  const userSelections = obj[user] || {};
  userSelections[itemKey] = !!isSelected;
  obj[user] = userSelections;
  writeShopSelectedItemsObject(obj);
}

export function clearShopSelectedItems(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readShopSelectedItemsObject();
  if (obj[user]) {
    delete obj[user];
    writeShopSelectedItemsObject(obj);
  }
}


export function getPurchasedItems(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readPurchasedObject();
  const arr = obj[user] || [];
  return Array.isArray(arr) ? arr : [];
}

export function addPurchasedItems(username, itemKeys) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readPurchasedObject();
  const current = Array.isArray(obj[user]) ? obj[user].slice() : [];
  const toAdd = Array.isArray(itemKeys) ? itemKeys : (itemKeys ? [itemKeys] : []);
  const set = new Set(current);
  for (const k of toAdd) {
    if (k != null && k !== '') set.add(k);
  }
  obj[user] = Array.from(set);
  writePurchasedObject(obj);
}

export function removePurchasedItem(username, itemKey) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readPurchasedObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  obj[user] = arr.filter(k => k !== itemKey);
  writePurchasedObject(obj);
}

export function clearPurchased(username) {
  const user = (username || getCurrentUsername() || 'guest');
  const obj = readPurchasedObject();
  if (obj[user]) {
    delete obj[user];
    writePurchasedObject(obj);
  }
}

// ----- Доставка auth helpers -----
export function isGroceryLoggedIn() {
  try {
    const val = lsGet(GROCERY_LOGIN_KEY);
    return val === 'true';
  } catch (e) {
    return false;
  }
}

export function setGroceryLoggedIn(value) {
  try {
    lsSet(GROCERY_LOGIN_KEY, value ? 'true' : 'false');
    if (value) clearExplicitLogout();
    else markExplicitLogout();
  } catch (e) {
  }
}

export function clearGroceryLogin() {
  try {
    lsRemove(GROCERY_LOGIN_KEY);
    lsRemove(GROCERY_USER_KEY);
    markExplicitLogout();
  } catch (e) {
  }
}

export function setGroceryCurrentUser(username) {
  try {
    lsSet(GROCERY_USER_KEY, username || '');
  } catch (e) {
  }
}

export function getGroceryCurrentUser() {
  try {
    return lsGet(GROCERY_USER_KEY) || '';
  } catch (e) {
    return '';
  }
}

// ----- Доставка basket storage (map of { itemId: quantity }) -----
function readGroceryBasketObject() {
  try {
    const raw = lsGet(GROCERY_BASKET_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeGroceryBasketObject(obj) {
  try {
    lsSet(GROCERY_BASKET_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

export function getGroceryBasket(username) {
  const user = (username || getGroceryCurrentUser() || 'guest');
  const obj = readGroceryBasketObject();
  const map = obj[user] || {};
  return map && typeof map === 'object' ? map : {};
}

export function setGroceryBasketItem(username, itemKey, quantity) {
  if (!itemKey) return;
  const user = (username || getGroceryCurrentUser() || 'guest');
  const obj = readGroceryBasketObject();
  const map = (obj[user] && typeof obj[user] === 'object') ? { ...obj[user] } : {};
  const q = Math.max(0, Number.isFinite(quantity) ? Math.floor(quantity) : 0);
  if (q <= 0) {
    if (map[itemKey] != null) delete map[itemKey];
  } else {
    map[itemKey] = q;
  }
  obj[user] = map;
  writeGroceryBasketObject(obj);
}

export function addGroceryBasketItem(username, itemKey, quantity) {
  const cur = getGroceryBasket(username);
  const prev = Number(cur[itemKey] || 0);
  const add = Math.max(1, Number.isFinite(quantity) ? Math.floor(quantity) : 1);
  setGroceryBasketItem(username, itemKey, prev + add);
}

export function incrementGroceryBasketItem(username, itemKey, delta) {
  const cur = getGroceryBasket(username);
  const prev = Number(cur[itemKey] || 0);
  const next = prev + (Number.isFinite(delta) ? Math.floor(delta) : 1);
  setGroceryBasketItem(username, itemKey, Math.max(0, next));
}

export function removeGroceryBasketItem(username, itemKey) {
  setGroceryBasketItem(username, itemKey, 0);
}

export function clearGroceryBasket(username) {
  const user = (username || getGroceryCurrentUser() || 'guest');
  const obj = readGroceryBasketObject();
  if (obj[user]) {
    delete obj[user];
    writeGroceryBasketObject(obj);
  }
}

export function getGroceryBasketCount(username) {
  const map = getGroceryBasket(username);
  return Object.values(map).reduce((sum, q) => sum + (Number.isFinite(q) ? q : 0), 0);
}

function mergeGroceryBasketUsers(fromUser, toUser) {
  if (!fromUser || !toUser || fromUser === toUser) return;
  const obj = readGroceryBasketObject();
  const fromMap = obj[fromUser];
  if (!fromMap || typeof fromMap !== 'object') return;

  const toMap = { ...(obj[toUser] && typeof obj[toUser] === 'object' ? obj[toUser] : {}) };
  let changed = false;
  Object.entries(fromMap).forEach(([itemId, qty]) => {
    const q = Number(qty) || 0;
    if (q <= 0) return;
    toMap[itemId] = (Number(toMap[itemId]) || 0) + q;
    changed = true;
  });
  if (!changed) return;

  obj[toUser] = toMap;
  delete obj[fromUser];
  writeGroceryBasketObject(obj);
}

/** Align grocery session user + migrate basket from legacy domain keys. */
export function syncGrocerySessionFromTrackConfig(trackConfig) {
  if (!isGroceryLoggedIn()) return;
  const expected = getBenchSessionUser(trackConfig);
  if (!expected) return;

  const legacyKeys = new Set();
  const current = getGroceryCurrentUser();
  if (current) legacyKeys.add(current);

  const domainRaw = trackConfig?.test_data?.user_data;
  const domain = Array.isArray(domainRaw) ? domainRaw[0] : domainRaw;
  if (domain && typeof domain === 'object') {
    if (domain.name) legacyKeys.add(domain.name);
    if (domain.email) legacyKeys.add(domain.email);
    if (domain.login) legacyKeys.add(domain.login);
  }

  const loginData = trackConfig?.test_data?.login_data || {};
  if (loginData.login) legacyKeys.add(loginData.login);

  legacyKeys.forEach((key) => {
    if (key && key !== expected) {
      mergeGroceryBasketUsers(key, expected);
    }
  });

  setGroceryCurrentUser(expected);
}

// ----- Доставка orders storage (array of order objects) -----
function readGroceryOrdersObject() {
  try {
    const raw = lsGet(GROCERY_ORDERS_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeGroceryOrdersObject(obj) {
  try {
    lsSet(GROCERY_ORDERS_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

export function pushGroceryOrder(username, order) {
  const user = (username || getGroceryCurrentUser() || 'guest');
  const obj = readGroceryOrdersObject();
  const arr = Array.isArray(obj[user]) ? obj[user].slice() : [];
  arr.push(order);
  obj[user] = arr;
  writeGroceryOrdersObject(obj);
}

// ----- RAIL auth helpers -----
export function isRailLoggedIn() {
  try {
    const val = lsGet(RAIL_LOGIN_KEY);
    return val === 'true';
  } catch (e) {
    return false;
  }
}

export function setRailLoggedIn(value) {
  try {
    lsSet(RAIL_LOGIN_KEY, value ? 'true' : 'false');
    if (value) clearExplicitLogout();
    else markExplicitLogout();
  } catch (e) {
  }
}

export function clearRailLogin() {
  try {
    lsRemove(RAIL_LOGIN_KEY);
    lsRemove(RAIL_USER_KEY);
    lsRemove(RAIL_USER_DATA_KEY);
    markExplicitLogout();
  } catch (e) {
  }
}

export function setRailCurrentUser(username) {
  try {
    lsSet(RAIL_USER_KEY, username || '');
  } catch (e) {
  }
}

export function getRailCurrentUser() {
  try {
    return lsGet(RAIL_USER_KEY) || '';
  } catch (e) {
    return '';
  }
}

function resolveBenchDomainViewType(trackConfig) {
  const cfg = trackConfig && typeof trackConfig === 'object' ? trackConfig : {};
  if (cfg.state_main?.view_type) {
    return cfg.state_main.view_type;
  }
  const domainKey = cfg.test_data?.active_bench_domain;
  const domains = cfg.domain_configs || {};
  const domainSlice = domainKey ? domains[domainKey] : null;
  if (domainSlice) {
    const mainState = Object.keys(domainSlice).find(
      (key) => key.startsWith('state_') && domainSlice[key]?.view_type?.includes('_main'),
    );
    if (mainState) {
      return domainSlice[mainState].view_type;
    }
  }
  for (const key of ['rail', 'grocery', 'shop', 'books']) {
    const slice = domains[key];
    const mainState = slice && Object.keys(slice).find(
      (stateKey) => stateKey.endsWith('_main') && slice[stateKey]?.view_type,
    );
    if (mainState) {
      return slice[mainState].view_type;
    }
  }
  return null;
}

function applyRailDefaultLogin(trackConfig) {
  const login = getBenchSessionUser(trackConfig);
  const passengers = getRailPassengers(trackConfig);
  setRailLoggedIn(true);
  setRailCurrentUser(login);
  setRailTicketLoggedIn(true);
  setRailTicketCurrentUser(login);
  if (passengers[0]) {
    setRailUserData(passengers[0]);
    setRailTicketUserData({
      ...passengers[0],
      passengers: passengers.slice(1),
    });
  }
}

function applyGroceryDefaultLogin(trackConfig, login) {
  setGroceryLoggedIn(true);
  setGroceryCurrentUser(isUnifiedBench(trackConfig) ? getBenchSessionUser(trackConfig) : login);
}

function applyShopBooksDefaultLogin(login) {
  setLoggedIn(true);
  setCurrentUsername(login);
}

/** Apply default logged-in session from track `test_data` (mock benchmarks). Idempotent. */
export function applyDefaultMockLoginFromTrackConfig(trackConfig) {
  try {
    const cfg = trackConfig && typeof trackConfig === 'object' ? trackConfig : {};
    const testData = cfg.test_data || {};
    if (!testData.login_data) return;
    if (testData.is_login === false) return;
    if (isExplicitLogout()) return;
    const login = getBenchSessionUser(trackConfig);
    if (isUnifiedBench(cfg)) {
      applyGroceryDefaultLogin(cfg, login);
      applyRailDefaultLogin(cfg);
      applyShopBooksDefaultLogin(login);
      return;
    }
    const viewType = resolveBenchDomainViewType(cfg);
    if (viewType === 'bench_grocery_main') {
      applyGroceryDefaultLogin(cfg, login);
    } else if (viewType === 'bench_rail_main') {
      applyRailDefaultLogin(cfg);
    } else {
      applyShopBooksDefaultLogin(login);
    }
  } catch (e) {
    // ignore
  }
}

export function syncRailLoggedInFromTrack(trackConfig) {
  applyDefaultMockLoginFromTrackConfig(trackConfig);
  return isRailLoggedIn();
}

export function syncRailTicketLoggedInFromTrack(trackConfig) {
  applyDefaultMockLoginFromTrackConfig(trackConfig);
  return isRailTicketLoggedIn();
}

export function syncMockLoggedInFromTrack(trackConfig) {
  applyDefaultMockLoginFromTrackConfig(trackConfig);
  const viewType = resolveBenchDomainViewType(trackConfig);
  if (viewType === 'bench_rail_main') {
    return isRailLoggedIn();
  }
  if (viewType === 'bench_grocery_main') {
    return isGroceryLoggedIn();
  }
  return isLoggedIn();
}

export function setRailUserData(userData) {
  try {
    lsSet(RAIL_USER_DATA_KEY, JSON.stringify(userData || {}));
  } catch (e) {
  }
}

export function getRailUserData() {
  try {
    const raw = lsGet(RAIL_USER_DATA_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

// ----- RAIL tickets basket storage -----
function readRzdTicketsObject() {
  try {
    const raw = lsGet(RAIL_TICKETS_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

function writeRzdTicketsObject(obj) {
  try {
    lsSet(RAIL_TICKETS_KEY, JSON.stringify(obj || {}));
  } catch (e) {
  }
}

export function getRailTickets(username) {
  const user = (username || getRailCurrentUser() || 'guest');
  const obj = readRzdTicketsObject();
  const arr = obj[user] || [];
  return Array.isArray(arr) ? arr : [];
}

export function addRailTicket(username, ticket) {
  if (!ticket) return;
  const user = (username || getRailCurrentUser() || 'guest');
  const obj = readRzdTicketsObject();
  const arr = Array.isArray(obj[user]) ? obj[user].slice() : [];
  // Add unique id if not present
  const ticketWithId = { ...ticket, id: ticket.id || `ticket_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` };
  arr.push(ticketWithId);
  obj[user] = arr;
  writeRzdTicketsObject(obj);
  return ticketWithId.id;
}

export function updateRailTicket(username, ticketId, updates) {
  if (!ticketId) return;
  const user = (username || getRailCurrentUser() || 'guest');
  const obj = readRzdTicketsObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  const idx = arr.findIndex(t => t && t.id === ticketId);
  if (idx !== -1) {
    arr[idx] = { ...arr[idx], ...updates };
    obj[user] = arr;
    writeRzdTicketsObject(obj);
  }
}

export function removeRailTicket(username, ticketId) {
  if (!ticketId) return;
  const user = (username || getRailCurrentUser() || 'guest');
  const obj = readRzdTicketsObject();
  const arr = Array.isArray(obj[user]) ? obj[user] : [];
  obj[user] = arr.filter(t => t && t.id !== ticketId);
  writeRzdTicketsObject(obj);
}

export function clearRailTickets(username) {
  const user = (username || getRailCurrentUser() || 'guest');
  const obj = readRzdTicketsObject();
  if (obj[user]) {
    delete obj[user];
    writeRzdTicketsObject(obj);
  }
}

export function getRailTicketsCount(username) {
  const arr = getRailTickets(username);
  return Array.isArray(arr) ? arr.length : 0;
}

// ----- RAIL booking session (temporary state during booking flow) -----
export function getRailBookingSession() {
  try {
    const raw = lsGet(RAIL_BOOKING_SESSION_KEY);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : null;
  } catch (e) {
    return null;
  }
}

export function setRailBookingSession(session) {
  try {
    lsSet(RAIL_BOOKING_SESSION_KEY, JSON.stringify(session || {}));
  } catch (e) {
  }
}

export function clearRailBookingSession() {
  try {
    lsRemove(RAIL_BOOKING_SESSION_KEY);
  } catch (e) {
  }
}

// ----- RAIL Ticket auth helpers (separate from main page login) -----
export function isRailTicketLoggedIn() {
  try {
    const val = lsGet(RAIL_TICKET_LOGIN_KEY);
    return val === 'true';
  } catch (e) {
    return false;
  }
}

export function setRailTicketLoggedIn(value) {
  try {
    lsSet(RAIL_TICKET_LOGIN_KEY, value ? 'true' : 'false');
    if (value) clearExplicitLogout();
    else markExplicitLogout();
  } catch (e) {
  }
}

export function clearRailTicketLogin() {
  try {
    lsRemove(RAIL_TICKET_LOGIN_KEY);
    lsRemove(RAIL_TICKET_USER_KEY);
    lsRemove(RAIL_TICKET_USER_DATA_KEY);
    markExplicitLogout();
  } catch (e) {
  }
}

export function setRailTicketCurrentUser(username) {
  try {
    lsSet(RAIL_TICKET_USER_KEY, username || '');
  } catch (e) {
  }
}

export function getRailTicketCurrentUser() {
  try {
    return lsGet(RAIL_TICKET_USER_KEY) || '';
  } catch (e) {
    return '';
  }
}

export function setRailTicketUserData(userData) {
  try {
    lsSet(RAIL_TICKET_USER_DATA_KEY, JSON.stringify(userData || {}));
  } catch (e) {
  }
}

export function getRailTicketUserData() {
  try {
    const raw = lsGet(RAIL_TICKET_USER_DATA_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (e) {
    return {};
  }
}

export default {
  hasPromptBeenSeen,
  markPromptSeen,
  clearPromptFlag,
  isLoggedIn,
  setLoggedIn,
  clearLogin,
  setCurrentUsername,
  getCurrentUsername,
  getBasketItems,
  addBasketItem,
  removeBasketItem,
  clearBasket,
  getShopFavorites,
  addShopFavorite,
  removeShopFavorite,
  toggleShopFavorite,
  clearShopFavorites,
  getShopFavoritesCount,
  getBooksFavorites,
  isBooksFavorite,
  addBooksFavorite,
  removeBooksFavorite,
  toggleBooksFavorite,
  clearBooksFavorites,
  getBooksFavoritesCount,
  getShopSelectedItems,
  setShopSelectedItems,
  setShopItemSelected,
  clearShopSelectedItems,
  getPurchasedItems,
  addPurchasedItems,
  removePurchasedItem,
  clearPurchased,
  isRailLoggedIn,
  setRailLoggedIn,
  clearRailLogin,
  setRailCurrentUser,
  getRailCurrentUser,
  setRailUserData,
  getRailUserData,
  getRailTickets,
  addRailTicket,
  updateRailTicket,
  removeRailTicket,
  clearRailTickets,
  getRailTicketsCount,
  getRailBookingSession,
  setRailBookingSession,
  clearRailBookingSession,
  isRailTicketLoggedIn,
  setRailTicketLoggedIn,
  clearRailTicketLogin,
  setRailTicketCurrentUser,
  getRailTicketCurrentUser,
  setRailTicketUserData,
  getRailTicketUserData
};