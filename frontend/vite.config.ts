import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'

export default defineConfig(async () => {
  let frappeUIPlugin = null
  
  try {
    const frappeUIVite = await import('frappe-ui/vite')
    frappeUIPlugin = frappeUIVite.default({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      // Note: We intentionally do NOT set buildConfig.indexHtmlPath here.
      // Letting Vite overwrite www/workshop.html bakes in the current
      // hashed asset filenames, which then go stale on the next build
      // (or on a fresh install where the committed workshop.html no
      // longer matches the assets actually shipped/built). Instead, we
      // keep workshop.html as a pure Jinja template and have workshop.py
      // read the asset paths from the built public/frontend/index.html
      // (or the Vite manifest) at request time. See www/workshop.py.
    })
  } catch (e) {
    console.warn('frappe-ui/vite not available:', e)
  }

  const plugins = frappeUIPlugin 
    ? [frappeUIPlugin, vue(), vueJsx()] 
    : [vue(), vueJsx()]

  return {
    define: {
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
    },
    plugins,
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    optimizeDeps: {
      include: ['frappe-ui', 'feather-icons'],
    },
    server: {
      port: 8080,
    },
    build: {
      outDir: '../car_repair_management/public/frontend',
      emptyOutDir: true,
      sourcemap: true,
      // Emit .vite/manifest.json so the server-side workshop.py can
      // resolve the current hashed entry filenames at request time
      // without depending on parsing index.html.
      manifest: true,
    },
  }
})
