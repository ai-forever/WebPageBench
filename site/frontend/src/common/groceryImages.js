import { resolveAssetUrl } from '@/common/cdnUrls';

/** Product photo from KV (title + img_url). */
export function groceryImageSrc(itemOrUrl) {
  const url = typeof itemOrUrl === 'string'
    ? itemOrUrl
    : (itemOrUrl && (itemOrUrl.img_url || itemOrUrl.img || itemOrUrl.thumbnail)) || '';
  return resolveAssetUrl(url) || '';
}
