import { create } from 'zustand'
import { authAPI } from '../api/auth'

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: false, // Start as false since we're not using JWT auth
  error: null,

  // Check if user is authenticated (either by token or recruiter_id)
  isAuthenticated: () => {
    const hasUser = get().user !== null
    const hasToken = get().token !== null
    const hasRecruiterId = localStorage.getItem('recruiter_id') !== null
    // In local demo, we allow access if we have any form of ID
    return hasUser || hasToken || hasRecruiterId
  },

  // Force re-render by updating state
  refreshAuth: () => {
    set((state) => ({ ...state }))
  },

  login: async (email, password) => {
    try {
      set({ loading: true, error: null })
      const response = await authAPI.login(email, password)

      const { token, user } = response
      localStorage.setItem('token', token)

      set({
        user,
        token,
        loading: false,
        error: null
      })

      return { success: true }
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Login failed'
      })
      return { success: false, error: error.response?.data?.message }
    }
  },

  loginByIdentity: async (identity) => {
    try {
      set({ loading: true, error: null })
      const response = await authAPI.loginByIdentity(identity)

      const { access_token, user } = response
      localStorage.setItem('token', access_token)
      localStorage.setItem('recruiter_id', user.id) // Maintain compatibility with existing App.jsx check

      set({
        user,
        token: access_token,
        loading: false,
        error: null
      })

      return { success: true }
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Identity verification failed'
      })
      return { success: false, error: error.response?.data?.message }
    }
  },

  register: async (email, password, fullName, company) => {
    try {
      set({ loading: true, error: null })
      const response = await authAPI.register(email, password, fullName, company)

      const { token, user } = response
      localStorage.setItem('token', token)

      set({
        user,
        token,
        loading: false,
        error: null
      })

      return { success: true }
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Registration failed'
      })
      return { success: false, error: error.response?.data?.message }
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('recruiter_id')
    set({
      user: null,
      token: null,
      loading: false,
      error: null
    })
  },

  checkAuth: async () => {
    const token = get().token
    if (!token) {
      set({ loading: false })
      return
    }

    try {
      const response = await authAPI.getProfile()
      set({
        user: response,
        loading: false,
        error: null
      })
    } catch (error) {
      // Don't clear session in dev mode if it's just a token expiry
      console.warn('Auth profile check failed, keeping session if possible')
      set({ loading: false })
    }
  },

  clearError: () => set({ error: null })
}))

export { useAuthStore }