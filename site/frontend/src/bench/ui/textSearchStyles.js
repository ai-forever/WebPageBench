/** CSS class suffixes for text_search UI variants. */

export const TEXT_SEARCH_VARIANT_CLASSES = {
  standard: '',
  outlined: 'bench-search--outlined',
  filled: 'bench-search--filled',
  underlined: 'bench-search--underlined',
  pill: 'bench-search--pill',
  large: 'bench-search--large',
};

export function textSearchVariantClass(variant) {
  return TEXT_SEARCH_VARIANT_CLASSES[variant] || '';
}

export function vuetifyFieldVariant(variant) {
  const map = {
    standard: 'outlined',
    outlined: 'outlined',
    filled: 'filled',
    underlined: 'underlined',
    pill: 'solo-filled',
    large: 'outlined',
  };
  return map[variant] || 'outlined';
}
