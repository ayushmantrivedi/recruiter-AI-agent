import { create } from 'zustand'
import { authAPI } from '../api/auth'

const useAuthStore = create((set, get) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: true,
  error: null,

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
      localStorage.removeItem('token')
      set({
        user: null,
        token: null,
        loading: false,
        error: null
      })
    }
  },

  clearError: () => set({ error: null })
}))

export { useAuthStore }