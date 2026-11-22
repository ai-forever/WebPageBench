import {
  fileURLToPath,
  URL
} from 'node:url'

import {
  defineConfig
} from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify';

// https://vitejs.dev/config/
function prefixAbsolutePublicPaths() {
  const base = String(process.env.VITE_BASE || '/').replace(/\/$/, '');
  if (!base) return null;
  const pattern = /(['"`(])\/(hotels|shop|books|grocery|rail|mocks)\//g;
  return {
    name: 'prefix-public-urls',
    enforce: 'pre',
    transform(code, id) {
      if (id.includes('node_modules')) return null;
      pattern.lastIndex = 0;
      if (!pattern.test(code)) return null;
      pattern.lastIndex = 0;
      return code.replace(pattern, `$1${base}/$2/`);
    },
  };
}

export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [prefixAbsolutePublicPaths(), vue(), vuetify({ autoImport: { labs: true } })].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src',
        import.meta.url))
    }
  }
})