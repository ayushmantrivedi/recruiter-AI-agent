import { api } from './client'

export const agentAPI = {
  runQuery: async (query, recruiterId = null) => {
    const response = await api.post('/api/recruiter/query', {
      query,
      recruiter_id: recruiterId
    })
    return response.data
  },

  getQueryStatus: async (queryId) => {
    const response = await api.get(`/api/recruiter/query/${queryId}`)
    return response.data
  },

  getQueryHistory: async (recruiterId = null) => {
    const params = recruiterId ? { recruiter_id: recruiterId } : {}
    const response = await api.get('/api/recruiter/queries', { params })
    return response.data
  }
}