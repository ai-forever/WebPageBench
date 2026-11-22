/** Catalog images are vendored under /shop/cdn, /grocery/cdn, /books/cdn. Do not remap to vendor CDNs. */

const REPLACEMENTS = [];

const IMAGE_KEYS = new Set([
  'img',
  'img_url',
  'cover_img_url',
  'thumbnail',
  'image',
  'imageUrl',
  'images',
  'src',
  'detail_img_urls',
  'gallery_urls',
]);

export function rewriteMediaUrl(url) {
  if (typeof url !== 'string' || !url) return url || '';
  if (url.startsWith('/') || url.startsWith('data:')) return url;
  let out = url;
  for (const [re, to] of REPLACEMENTS) {
    out = out.replace(re, to);
  }
  return out;
}

const PUBLIC_ASSET = /^\/(?:shop|books|grocery|hotels|rail|mocks)(?:\/|$)/;

function withPublicBase(path) {
  const base = String(import.meta.env.BASE_URL || '/');
  const normalized = base.endsWith('/') ? base.slice(0, -1) : base;
  if (!path.startsWith('/') || !normalized) return path;
  if (path === normalized || path.startsWith(`${normalized}/`)) return path;
  return `${normalized}${path}`;
}

/** Public-folder paths (/shop/cdn/…) stay as-is on the site root; remote URLs go through rewriteMediaUrl. */
export function resolveAssetUrl(src) {
  if (!src) return '';
  const s = String(src);
  if (s.startsWith('data:')) return s;
  if (s.startsWith('/')) return withPublicBase(s);
  if (/^https?:/i.test(s)) return rewriteMediaUrl(s);
  return s;
}

export function rewriteMediaTree(value, key) {
  if (Array.isArray(value)) {
    return value.map((item) => rewriteMediaTree(item, key));
  }
  if (value && typeof value === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(value)) {
      out[k] = rewriteMediaTree(v, k);
    }
    return out;
  }
  if (typeof value !== 'string') return value;
  if (PUBLIC_ASSET.test(value)) return withPublicBase(value);
  if (key && IMAGE_KEYS.has(key)) return resolveAssetUrl(value);
  if (/\/(cover|product_card|pub\/c\/cover|dam-storage)/i.test(value)) return rewriteMediaUrl(value);
  return value;
}
