import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Grid, List, Download, Filter, Search, Sparkles, TrendingUp, Users } from 'lucide-react';
import LeadTable from '../components/LeadTable.jsx';
import LeadCard from '../components/LeadCard.jsx';
import { useLeadStore } from '../store/leadStore.js';
import { useAuthStore } from '../store/authStore.js';

const Leads = () => {
  const [viewMode, setViewMode] = useState('table');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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

  const stats = (() => {
    const total = leads.length;
    const highScore = leads.filter(lead => lead.score >= 80).length;
    const avgScore = total > 0
      ? Math.round(leads.reduce((sum, lead) => sum + lead.score, 0) / total)
      : 0;
    return { total, highScore, avgScore };
  })();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-accent-indigo"></div>
        <p className="text-slate-400 animate-pulse">Retrieving market intelligence...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 pb-32">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold text-white tracking-tight">Intelligence Bank</h1>
          <p className="text-slate-400 mt-2 text-lg">
            A curated repository of high-signal hiring leads discovered by your agents.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
            <button
              onClick={() => setViewMode('table')}
              className={`p-2.5 rounded-lg transition-all ${viewMode === 'table' ? 'bg-accent-indigo text-white shadow-lg' : 'text-slate-400 hover:text-white'
                }`}
            >
              <List className="h-5 w-5" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`p-2.5 rounded-lg transition-all ${viewMode === 'cards' ? 'bg-accent-indigo text-white shadow-lg' : 'text-slate-400 hover:text-white'
                }`}
            >
              <Grid className="h-5 w-5" />
            </button>
          </div>

          {leads.length > 0 && (
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 rounded-xl text-white font-semibold hover:bg-white/10 transition-all"
            >
              <Download className="h-5 w-5 text-accent-emerald" />
              <span>Export CSV</span>
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: 'Total Leads', value: stats.total, icon: <Users />, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
          { label: 'Prime Targets', value: stats.highScore, icon: <Sparkles />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
          { label: 'Avg Match', value: `${stats.avgScore}%`, icon: <TrendingUp />, color: 'text-amber-400', bg: 'bg-amber-500/10' },
        ].map((stat, i) => (
          <div key={i} className="glass-card p-6 flex items-center justify-between border-white/5">
            <div>
              <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{stat.label}</p>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
            </div>
            <div className={`p-4 ${stat.bg} ${stat.color} rounded-2xl`}>
              {stat.icon}
            </div>
          </div>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="glass-card p-6 border-red-500/20 bg-red-500/5 flex items-center justify-between">
          <div className="flex items-center gap-4 text-red-400">
            <Filter className="h-6 w-6" />
            <p className="font-medium">{error}</p>
          </div>
          <button onClick={clearError} className="text-slate-400 hover:text-white underline text-sm">Dismiss</button>
        </div>
      )}

      {/* Leads Content Area */}
      <div className="glass-card overflow-hidden">
        {leads.length > 0 ? (
          <div className="p-1">
            {viewMode === 'table' ? (
              <div className="overflow-x-auto">
                <LeadTable
                  leads={leads}
                  onFeedback={handleFeedback}
                  onExport={handleExport}
                />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
                {leads.map((lead) => (
                  <LeadCard
                    key={lead.id}
                    lead={lead}
                    onFeedback={handleFeedback}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-24 px-8">
            <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6">
              <Search className="h-10 w-10 text-slate-600" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">The reservoir is empty</h3>
            <p className="text-slate-400 mb-8 max-w-md mx-auto">
              You haven't discovered any hiring leads yet. Deploy your first intelligence agent to start scanning the market.
            </p>
            <button
              onClick={() => navigate('/run-agent')}
              className="btn-primary"
            >
              Deploy First Agent
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Leads;
