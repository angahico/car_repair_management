import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { FrappeUI, setConfig } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import { frappeRequest } from './api/client'
import { messages } from './locales'
import './index.css'

const savedLocale = localStorage.getItem('workshop-locale') || 'en'
const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages,
})

// Set document direction for RTL languages
const rtlLocales = ['ar']
document.documentElement.dir = rtlLocales.includes(savedLocale) ? 'rtl' : 'ltr'

const pinia = createPinia()
const app = createApp(App)

// Use our custom frappeRequest that includes credentials
setConfig('resourceFetcher', frappeRequest)

app.use(i18n)
app.use(FrappeUI)
app.use(pinia)
app.use(router)

// Initialize app with dev context if needed
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/car_repair_management.www.workshop.get_context_for_dev', method: 'GET' })
    .then((result: any) => {
      const values = result?.message || result || {}
      for (const key in values) {
        (window as any)[key] = values[key]
      }
      app.mount('#app')
    })
    .catch(() => {
      // Fallback if endpoint doesn't exist
      app.mount('#app')
    })
} else {
  app.mount('#app')
}
