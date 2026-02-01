import { api } from './client'

export const metricsAPI = {
  getDashboardMetrics: async () => {
    const response = await api.get('/api/recruiter/metrics/dashboard')
    return response.data
  },

  getUsageMetrics: async (period = '30d') => {
    const response = await api.get('/api/recruiter/metrics/usage', {
      params: { period }
    })
    return response.data
  },

  getPerformanceMetrics: async () => {
    const response = await api.get('/api/recruiter/metrics/performance')
    return response.data
  }
}