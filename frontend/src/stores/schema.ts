import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { discoverSchema, loadSchemaFromStorage, saveSchemaToStorage } from '@/schema'
import type { SchemaRegistry, DoctypeMeta } from '@/schema'

export const useSchemaStore = defineStore('workshop-schema', () => {
  const registry = ref<SchemaRegistry | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)

  // Ready when initialized (even if discovery failed or returned empty)
  const isReady = computed(() => initialized.value)

  const availableDoctypes = computed(() => {
    if (!registry.value) return []
    return Object.keys(registry.value.doctypes)
  })

  function getDoctype(name: string): DoctypeMeta | null {
    return registry.value?.doctypes[name] || null
  }

  function hasDoctype(name: string): boolean {
    return !!registry.value?.doctypes[name]
  }

  async function initialize() {
    if (initialized.value) return
    
    // Try loading from storage first
    const stored = loadSchemaFromStorage()
    if (stored) {
      registry.value = stored
      initialized.value = true
      
      // Refresh in background if older than 1 hour
      const age = Date.now() - new Date(stored.discoveredAt).getTime()
      if (age > 60 * 60 * 1000) {
        refresh()
      }
      return
    }

    await refresh()
    initialized.value = true
  }

  async function refresh() {
    isLoading.value = true
    error.value = null
    
    try {
      const discovered = await discoverSchema()
      registry.value = discovered
      saveSchemaToStorage(discovered)
      console.log('Schema discovery complete:', Object.keys(discovered.doctypes))
    } catch (e) {
      console.error('Schema discovery failed:', e)
      error.value = e instanceof Error ? e.message : 'Failed to discover schema'
      // Set empty registry so app can still function
      registry.value = { doctypes: {}, domains: {}, discoveredAt: new Date().toISOString() }
    } finally {
      isLoading.value = false
    }
  }

  return {
    registry,
    isLoading,
    error,
    isReady,
    initialized,
    availableDoctypes,
    getDoctype,
    hasDoctype,
    initialize,
    refresh,
  }
})
