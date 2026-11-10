import {
  createApp
} from 'vue'
import App from './App.vue'
import router from './router'
import {
  loadFonts
} from './plugins/webfontloader'
import {
  createVuetify
} from 'vuetify'
import store from '@/store'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import ApiService from "@/common/api.service";

// import axios from "axios";
import VueAxios from "vue-axios";

// Styles
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
// Plain imports, not <style src>. vite-plugin-vue caches one descriptor per
// shared stylesheet and can scope it to the last SFC that referenced it.
// That drops market and books layout in the production build used by eval.
import '@/assets/shop.css'
import '@/assets/books.css'

loadFonts()

const vuetify = createVuetify({
  components,
  directives,
})

ApiService.init();

createApp(App)
  .use(router)
  .use(vuetify)
  .use(store)
  .use(VueAxios)
  // .use(axios)
  .mount('#app')