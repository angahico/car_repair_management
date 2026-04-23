import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export const useSessionStore = defineStore('workshop-session', () => {
  function getSessionUser(): string | null {
    const cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    const userId = cookies.get('user_id')
    return userId && userId !== 'Guest' ? userId : null
  }

  const user = ref<string | null>(getSessionUser())
  const isLoggedIn = computed(() => !!user.value)

  const login = createResource({
    url: 'login',
    onError() {
      throw new Error('Invalid email or password')
    },
    onSuccess() {
      user.value = getSessionUser()
      login.reset()
      window.location.href = '/workshop'
    },
  })

  const logout = createResource({
    url: 'logout',
    onSuccess() {
      user.value = null
      window.location.href = '/login?redirect-to=/workshop'
    },
  })

  function refreshUser() {
    user.value = getSessionUser()
  }

  return {
    user,
    isLoggedIn,
    login,
    logout,
    refreshUser,
  }
})
