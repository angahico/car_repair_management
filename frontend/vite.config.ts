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
      buildConfig: {
        indexHtmlPath: '../car_repair_management/www/workshop.html',
      },
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
    },
  }
})
