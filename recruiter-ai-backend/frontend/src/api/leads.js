import { api } from './client'

export const leadsAPI = {
  getLeads: async (params = {}) => {
    const response = await api.get('/api/recruiter/leads', { params })
    return response.data
  },

  getLeadById: async (id) => {
    const response = await api.get(`/api/recruiter/leads/${id}`)
    return response.data
  },

  submitFeedback: async (leadId, rating, feedback = '') => {
    const response = await api.post(`/api/recruiter/feedback`, {
      lead_id: leadId,
      rating,
      feedback
    })
    return response.data
  },

  exportLeads: async (format = 'csv') => {
    const response = await api.get('/api/recruiter/leads/export', {
      params: { format },
      responseType: 'blob'
    })
    return response.data
  }
}