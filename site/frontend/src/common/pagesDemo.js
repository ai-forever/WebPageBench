import { DataService } from "@/common/api.service";
import { rewriteMediaTree } from "@/common/cdnUrls";

const PUBLIC_ASSET = /^\/(?:shop|books|grocery|hotels|rail|mocks)(?:\/|$)/;
const eventsByTrack = new Map();
let eventSeq = 1;

function demoAsset(path) {
  const base = import.meta.env.BASE_URL || "/";
  return `${base.replace(/\/?$/, "/")}${path.replace(/^\//, "")}`;
}

function withPublicBase(path) {
  const base = String(import.meta.env.BASE_URL || "/");
  const normalized = base.endsWith("/") ? base.slice(0, -1) : base;
  if (!path.startsWith("/") || !normalized) return path;
  if (path === normalized || path.startsWith(`${normalized}/`)) return path;
  return `${normalized}${path}`;
}

let trackPromise;
const kvPromises = new Map();

function loadTrack() {
  if (!trackPromise) {
    trackPromise = fetch(demoAsset("pages-demo/track.json")).then((response) => {
      if (!response.ok) throw new Error("pages demo track");
      return response.json();
    });
  }
  return trackPromise;
}

function loadJson(path) {
  if (!kvPromises.has(path)) {
    kvPromises.set(
      path,
      fetch(demoAsset(path)).then((response) => {
        if (!response.ok) throw new Error(path);
        return response.json();
      }),
    );
  }
  return kvPromises.get(path);
}

function safeKvPath(kvPath) {
  const raw = String(kvPath || "").replace(/\\/g, "/").replace(/^\/+/, "");
  if (!raw || raw.includes("..")) return "";
  return raw;
}

function rememberEvent(trackId, eventName, eventData) {
  const raw = String(eventData || "");
  if (raw.includes("pages-demo-events") || raw.includes("pages-demo-theme")) return;
  const row = {
    id: eventSeq,
    event_id: `demo-${eventSeq}`,
    event_name: eventName || "event",
    event_data: eventData,
    event_ts: new Date().toISOString(),
    trackId: trackId || "",
  };
  eventSeq += 1;
  const list = eventsByTrack.get(row.trackId) || [];
  list.push(row);
  eventsByTrack.set(row.trackId, list.slice(-200));
  window.dispatchEvent(new CustomEvent("pages-demo-events"));
}

export function pagesDemoEventList() {
  const rows = [];
  for (const list of eventsByTrack.values()) rows.push(...list);
  return rows;
}

function prefixRenderedAssets() {
  const base = String(import.meta.env.BASE_URL || "/");
  if (base === "/") return;
  const fix = (node) => {
    if (!(node instanceof Element)) return;
    for (const attr of ["src", "href"]) {
      const value = node.getAttribute(attr);
      if (value && PUBLIC_ASSET.test(value)) {
        const next = withPublicBase(value);
        if (next !== value) node.setAttribute(attr, next);
      }
    }
  };
  const scan = (root) => {
    fix(root);
    if (root instanceof Element) root.querySelectorAll("[src],[href]").forEach(fix);
  };
  const start = () => {
    scan(document.body);
    new MutationObserver((records) => {
      for (const record of records) {
        if (record.type === "attributes") fix(record.target);
        for (const node of record.addedNodes) scan(node);
      }
    }).observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["src", "href"],
    });
  };
  if (document.body) start();
  else document.addEventListener("DOMContentLoaded", start);
}

/** Serve the bench from static JSON so the built SPA works without the API. */
export function installPagesDemo() {
  if (import.meta.env.VITE_PAGES_DEMO !== "1") return;
  import("./pagesDemo.css");
  prefixRenderedAssets();

  DataService.getTrackConfig = async (params) => {
    const config = rewriteMediaTree(structuredClone(await loadTrack()));
    const trackId = String((params && params.trackId) || "");
    const dark = /(?:^|[-_])dark$/.test(trackId) || trackId.includes("theme_dark");
    config.test_data = config.test_data || {};
    config.test_data.ui_variants = {
      ...(config.test_data.ui_variants || {}),
      theme: dark ? "dark" : "light",
    };
    return {
      data: {
        config: JSON.stringify(config),
        track_mtime: "pages-demo",
      },
    };
  };

  DataService.getKvStore = async (params) => {
    const kvPath = safeKvPath(params && params.kvPath);
    if (!kvPath) return { data: { kv_store: "{}" } };
    try {
      const kv = rewriteMediaTree(await loadJson(`pages-demo/kv/${kvPath}`));
      return { data: { kv_store: JSON.stringify(kv) } };
    } catch (error) {
      console.warn("[pages-demo] catalog missing", kvPath, error);
      return { data: { kv_store: "{}" } };
    }
  };

  DataService.getGroceryCategory = async (params) => {
    const requested = String((params && params.categoryId) || "tantsuyut_vse");
    const safe = requested.replace(/[^a-zA-Z0-9_-]/g, "") || "tantsuyut_vse";
    let category;
    try {
      category = await loadJson(`pages-demo/grocery/${safe}.json`);
    } catch (error) {
      category = await loadJson("pages-demo/grocery/tantsuyut_vse.json");
    }
    return { data: { category: JSON.stringify(category) } };
  };

  DataService.sendEvent = async (params) => {
    rememberEvent(params && params.trackId, params && params.eventName, params && params.eventData);
    return { data: { ok: true } };
  };

  DataService.getEvents = async (params) => {
    const trackId = String((params && params.trackId) || "");
    const events = trackId ? (eventsByTrack.get(trackId) || []) : pagesDemoEventList();
    return { data: { events } };
  };
}
