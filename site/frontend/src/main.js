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