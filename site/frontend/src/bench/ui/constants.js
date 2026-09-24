/** UI taxonomy widget variant IDs (docs/UI_TAXONOMY.md). */

export const UI_VARIANT_DEFAULTS = {
  date: 'split_popup',
  select_city: 'autocomplete',
  select_station: 'typeahead',
  counter_guests: 'rooms_popup',
  text_search: 'standard',
  collections: 'cards',
  years: 'select',
  buttons: 'outline',
  theme: 'light',
};

export const UI_VARIANT_IDS = {
  date: ['split_popup', 'inline_calendar', 'text_input', 'single_popup', 'popup_grid', 'native_input'],
  select_city: ['autocomplete', 'native_select'],
  select_station: ['typeahead', 'native_select'],
  counter_guests: ['rooms_popup', 'inline_stepper', 'compact_select', 'pill_buttons'],
  text_search: ['standard', 'outlined', 'filled', 'underlined', 'pill', 'large'],
  collections: ['cards', 'list', 'tree', 'compact'],
  years: ['select', 'buttons', 'radio'],
  buttons: ['solid', 'outline', 'icon', 'split'],
  theme: ['light', 'dark'],
};

/** Maps widget keys to UI taxonomy class IDs (docs/UI_TAXONOMY.md §2). */
export const WIDGET_TAXONOMY_CLASS = {
  date: 'DATE',
  select_city: 'SELECT_AC',
  select_station: 'SELECT_LIST',
  counter_guests: 'COUNTER',
  text_search: 'TXT',
  collections: 'CARD',
  years: 'SELECT_LIST',
  buttons: 'BTN',
};
