import { DataService } from "@/common/api.service";

const TASK = "В «Маркете» найдите сухой корм Purina ONE для стерилизованных кошек с говядиной и пшеницей и добавьте в корзину.";

function demoAsset(path) {
  const base = import.meta.env.BASE_URL || "/";
  return `${base.replace(/\/?$/, "/")}${path.replace(/^\//, "")}`;
}

let trackPromise;
let kvPromise;

function loadTrack() {
  if (!trackPromise) {
    trackPromise = fetch(demoAsset("pages-demo/track.json")).then((response) => {
      if (!response.ok) throw new Error("pages demo track");
      return response.json();
    });
  }
  return trackPromise;
}

function loadKv() {
  if (!kvPromise) {
    kvPromise = fetch(demoAsset("pages-demo/shop_kv.json")).then((response) => {
      if (!response.ok) throw new Error("pages demo catalog");
      return response.json();
    });
  }
  return kvPromise;
}

/** Serve the market from static JSON so the built SPA works without the API. */
export function installPagesDemo() {
  if (import.meta.env.VITE_PAGES_DEMO !== "1") return;

  DataService.getTrackConfig = async (params) => {
    const config = structuredClone(await loadTrack());
    const trackId = String((params && params.trackId) || "");
    const dark = /(?:^|[-_])dark$/.test(trackId) || trackId.includes("theme_dark");
    config.test_data = config.test_data || {};
    config.test_data.task = TASK;
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

  DataService.getKvStore = async () => {
    const kv = await loadKv();
    return { data: { kv_store: JSON.stringify(kv) } };
  };

  DataService.sendEvent = async () => ({ data: { ok: true } });
  DataService.getEvents = async () => ({ data: { events: [] } });
}
