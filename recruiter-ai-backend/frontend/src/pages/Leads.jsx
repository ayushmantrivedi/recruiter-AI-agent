import { useEffect, useState } from 'react';
import { Grid, List, Download, Filter } from 'lucide-react';
import LeadTable from '../components/LeadTable.jsx';
import LeadCard from '../components/LeadCard.jsx';
import useLeadStore from '../store/leadStore.js';
import useAuthStore from '../store/authStore.js';

const Leads = () => {
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'cards'
  const [isLoading, setIsLoading] = useState(false);

  const { user } = useAuthStore();
  const {
    leads,
    fetchLeads,
    submitFeedback,
    exportLeads,
    error,
    clearError
  } = useLeadStore();

  useEffect(() => {
    const loadLeads = async () => {
      setIsLoading(true);
      try {
        await fetchLeads();
      } catch (error) {
        console.error('Failed to fetch leads:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadLeads();
  }, [fetchLeads]);

  const handleFeedback = async (leadId, rating) => {
    try {
      const result = await submitFeedback(leadId, rating);
      if (!result.success) {
        console.error('Feedback submission failed:', result.error);
      }
    } catch (error) {
      console.error('Feedback submission error:', error);
    }
  };

  const handleExport = async () => {
    try {
      await exportLeads(user?.id);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getStats = () => {
    const total = leads.length;
    const highScore = leads.filter(lead => lead.score >= 80).length;
    const avgScore = total > 0
      ? Math.round(leads.reduce((sum, lead) => sum + lead.score, 0) / total)
      : 0;

    return { total, highScore, avgScore };
  };

  const stats = getStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Hiring Leads</h1>
          <p className="text-gray-600 mt-1">
            AI-discovered companies actively hiring for your target roles
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="flex rounded-lg border border-gray-200 p-1">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded ${
                viewMode === 'table'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <List className="h-4 w-4" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`p-1.5 rounded ${
                viewMode === 'cards'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Grid className="h-4 w-4" />
            </button>
          </div>

          {/* Export Button */}
          {leads.length > 0 && (
            <button
              onClick={handleExport}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            >
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="stats-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stats-label">Total Leads</p>
              <p className="stats-number">{stats.total}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <List className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="stats-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stats-label">High-Score Leads</p>
              <p className="stats-number">{stats.highScore}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <Filter className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="stats-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stats-label">Average Score</p>
              <p className="stats-number">{stats.avgScore}</p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <Download className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="rounded-md bg-danger-50 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-danger-800">
                Error loading leads
              </h3>
              <div className="mt-2 text-sm text-danger-700">
                {error}
              </div>
              <div className="mt-4">
                <div className="-mx-2 -my-1.5 flex">
                  <button
                    onClick={clearError}
                    className="bg-danger-50 px-2 py-1.5 rounded-md text-sm font-medium text-danger-800 hover:bg-danger-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-danger-50 focus:ring-danger-600"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Leads Display */}
      {leads.length > 0 ? (
        viewMode === 'table' ? (
          <LeadTable
            leads={leads}
            onFeedback={handleFeedback}
            onExport={handleExport}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {leads.map((lead) => (
              <LeadCard
                key={lead.id}
                lead={lead}
                onFeedback={handleFeedback}
              />
            ))}
          </div>
        )
      ) : (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No leads yet</h3>
          <p className="text-gray-600 mb-4">
            Run the AI agent to discover companies actively hiring for your target roles.
          </p>
          <a
            href="/run-agent"
            className="btn-primary inline-flex items-center"
          >
            <List className="h-4 w-4 mr-2" />
            Run AI Agent
          </a>
        </div>
      )}
    </div>
  );
};

export default Leads;
