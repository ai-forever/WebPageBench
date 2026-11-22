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
function prefixBuiltPublicPaths() {
  const base = String(process.env.VITE_BASE || '/').replace(/\/$/, '');
  if (!base) return null;
  const rewrite = (source) => source.replace(
    /(['"`(])\/(hotels|shop|books|grocery|rail|mocks)\//g,
    `$1${base}/$2/`,
  );
  return {
    name: 'prefix-built-public-urls',
    apply: 'build',
    enforce: 'post',
    generateBundle(_options, bundle) {
      for (const item of Object.values(bundle)) {
        if (item.type === 'chunk') item.code = rewrite(item.code);
        else if (item.type === 'asset' && typeof item.source === 'string') item.source = rewrite(item.source);
      }
    },
  };
}

export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [vue(), vuetify({ autoImport: { labs: true } }), prefixBuiltPublicPaths()].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src',
        import.meta.url))
    }
  }
})