import { create } from 'zustand'
import { leadsAPI } from '../api/leads'
import { agentAPI } from '../api/agent'

const useLeadStore = create((set, get) => ({
  leads: [],
  currentLead: null,
  agentRuns: [],
  loading: false,
  error: null,

  // Fetch leads
  fetchLeads: async (params = {}) => {
    try {
      set({ loading: true, error: null })
      const response = await leadsAPI.getLeads(params)
      set({
        leads: response.leads || [],
        loading: false
      })
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Failed to fetch leads'
      })
    }
  },

  // Get lead by ID
  fetchLeadById: async (id) => {
    try {
      set({ loading: true, error: null })
      const response = await leadsAPI.getLeadById(id)
      set({
        currentLead: response,
        loading: false
      })
      return response
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Failed to fetch lead'
      })
      throw error
    }
  },

  // Run agent query
  runAgentQuery: async (query) => {
    try {
      set({ loading: true, error: null })
      const response = await agentAPI.runQuery(query)

      // Add to agent runs
      const runs = get().agentRuns
      set({
        agentRuns: [response, ...runs],
        loading: false
      })

      return response
    } catch (error) {
      set({
        loading: false,
        error: error.response?.data?.message || 'Failed to run agent query'
      })
      throw error
    }
  },

  // Check query status
  checkQueryStatus: async (queryId) => {
    try {
      const response = await agentAPI.getQueryStatus(queryId)

      // Update the run in agentRuns
      const runs = get().agentRuns
      const updatedRuns = runs.map(run =>
        run.query_id === queryId ? { ...run, ...response } : run
      )

      set({ agentRuns: updatedRuns })

      // If completed, refresh leads
      if (response.status === 'completed' && response.leads) {
        const currentLeads = get().leads
        set({ leads: [...response.leads, ...currentLeads] })
      }

      return response
    } catch (error) {
      console.error('Failed to check query status:', error)
      throw error
    }
  },

  // Submit feedback
  submitFeedback: async (leadId, rating, feedback = '') => {
    try {
      await leadsAPI.submitFeedback(leadId, rating, feedback)

      // Update lead in local state
      const leads = get().leads
      const updatedLeads = leads.map(lead =>
        lead.id === leadId
          ? { ...lead, feedback: { rating, feedback, submitted_at: new Date().toISOString() } }
          : lead
      )

      set({ leads: updatedLeads })

      if (get().currentLead?.id === leadId) {
        set({
          currentLead: {
            ...get().currentLead,
            feedback: { rating, feedback, submitted_at: new Date().toISOString() }
          }
        })
      }
    } catch (error) {
      throw error
    }
  },

  // Export leads
  exportLeads: async (format = 'csv') => {
    try {
      const data = await leadsAPI.exportLeads(format)

      // Create download link
      const url = window.URL.createObjectURL(new Blob([data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `leads.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      throw error
    }
  },

  clearError: () => set({ error: null }),

  setCurrentLead: (lead) => set({ currentLead: lead })
}))

export { useLeadStore }