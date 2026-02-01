import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLeadStore } from '../store/leadStore'
import { Zap, Loader, CheckCircle, AlertCircle, Sparkles, ArrowRight, TrendingUp } from 'lucide-react'

function RunAgent() {
  const [query, setQuery] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const { runAgentQuery, checkQueryStatus } = useLeadStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsRunning(true)
    setError(null)
    setResult(null)

    try {
      const response = await runAgentQuery(query.trim())
      setResult(response)

      if (response.status !== 'completed') {
        pollQueryStatus(response.query_id)
      } else {
        setIsRunning(false)
      }
    } catch (err) {
      setError(err.message || 'Failed to run search')
      setIsRunning(false)
    }
  }

  const pollQueryStatus = async (queryId) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await checkQueryStatus(queryId)
        setResult(status)

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          setIsRunning(false)
        }
      } catch (err) {
        console.error('Failed to check status:', err)
        clearInterval(pollInterval)
        setIsRunning(false)
        setError('Failed to check search status')
      }
    }, 2000)

    setTimeout(() => {
      clearInterval(pollInterval)
      setIsRunning(false)
    }, 120000)
  }

  const exampleQueries = [
    "Senior full-stack engineers in Austin",
    "Product designers with fintech experience",
    "Data scientists who know Python and ML",
    "Remote DevOps engineers for startups",
  ]

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-8 pb-32">
      {/* Header */}
      <header className="mb-12">
        <div className="flex items-center gap-4 mb-4">
          <div className="p-3 bg-gradient-to-br from-accent-coral to-primary-600 rounded-2xl shadow-lg shadow-accent-coral/30">
            <Zap className="h-7 w-7 text-white" stroke-width={2.5} />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-bold text-white">
              Find Talent
            </h1>
            <p className="text-slate-400 mt-2 text-lg">
              Describe your ideal candidate and we'll find them for you
            </p>
          </div>
        </div>
      </header>

      {/* Search Form */}
      <section className="glass-card p-8 glow-border">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-3">
            <label htmlFor="query" className="text-sm font-semibold text-slate-300">
              What kind of talent are you looking for?
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Example: Senior React developers in London with experience in financial services..."
              className="w-full h-36 input-field resize-none text-base"
              required
            />
            <p className="text-xs text-slate-500 ml-1">
              Be as specific as you'd like – location, skills, experience level, industry, etc.
            </p>
          </div>

          <button
            type="submit"
            disabled={isRunning || !query.trim()}
            className="btn-primary px-8 py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="flex items-center justify-center gap-3">
              {isRunning ? (
                <>
                  <Loader className="h-5 w-5 animate-spin" />
                  <span>Searching the market...</span>
                </>
              ) : (
                <>
                  <Zap className="h-5 w-5" />
                  <span>Start Search</span>
                </>
              )}
            </div>
          </button>
        </form>

        {/* Example Queries */}
        <div className="mt-8 pt-8 border-t border-slate-700/50">
          <p className="text-sm font-semibold text-slate-400 mb-4">
            Need inspiration? Try these:
          </p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                type="button"
                className="px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-slate-300 hover:bg-slate-700/50 hover:border-accent-coral/50 hover:text-white transition-all"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Results */}
      {result && (
        <div className="glass-card overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Result Header */}
          <div className="p-8 border-b border-slate-700/50 bg-gradient-to-r from-slate-900/60 to-slate-800/40">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl ${result.status === 'completed' ? 'bg-accent-teal/20 text-accent-teal' :
                    result.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      'bg-accent-purple/20 text-accent-purple'
                  }`}>
                  {result.status === 'completed' ? <CheckCircle className="h-6 w-6" /> :
                    result.status === 'failed' ? <AlertCircle className="h-6 w-6" /> :
                      <Loader className="h-6 w-6 animate-spin" />}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-white">Search Results</h2>
                  <p className="text-sm text-slate-500 mt-1">ID: {result.query_id?.slice(0, 8)}...</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-white">{result.leads ? result.leads.length : 0}</p>
                <p className="text-sm text-slate-400 font-semibold">Candidates</p>
              </div>
            </div>
          </div>

          {/* Result Content */}
          <div className="p-8 space-y-8 max-h-[600px] overflow-y-auto">
            {/* Synthesis Report */}
            {result.synthesis_report && (
              <div className="bg-gradient-to-br from-accent-purple/10 to-accent-teal/10 border border-accent-purple/20 rounded-2xl p-6 relative">
                <div className="absolute top-6 right-6 text-accent-purple/20">
                  <Sparkles className="h-10 w-10" />
                </div>
                <h3 className="text-accent-purple text-sm font-bold uppercase tracking-wider mb-4">
                  Market Summary
                </h3>
                <div className="text-slate-300 leading-relaxed space-y-2">
                  {result.synthesis_report.split('\n').map((line, i) => (
                    <p key={i} className="text-base">
                      {line.startsWith('#') ? <strong>{line.replace(/#/g, '')}</strong> : line}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {/* Leads List */}
            {result.status === 'completed' && result.leads && result.leads.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-white font-bold text-xl flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-accent-teal" />
                  Top Matches
                  <span className="text-slate-500 text-base font-normal">({result.leads.length})</span>
                </h3>
                <div className="grid gap-4">
                  {result.leads.map((lead, index) => (
                    <div
                      key={index}
                      className="group p-6 bg-gradient-to-br from-slate-900/60 to-slate-800/40 border border-slate-700/50 rounded-2xl hover:border-accent-coral/50 hover-lift cursor-pointer"
                      onClick={() => navigate(`/leads/${lead.id || lead.company}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-bold text-white text-xl mb-2">{lead.company}</p>
                          <div className="flex items-center gap-3 flex-wrap">
                            <span className="badge-coral">
                              Match: {lead.score}%
                            </span>
                            {lead.reasons?.[0] && (
                              <p className="text-slate-400 text-sm italic">
                                "{lead.reasons[0]}"
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="p-3 bg-accent-coral/10 text-accent-coral rounded-xl group-hover:bg-accent-coral group-hover:text-white transition-all">
                          <ArrowRight className="h-5 w-5" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Failed State */}
            {result.status === 'failed' && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-red-400">
                <p className="font-bold mb-2 text-lg">Search Failed</p>
                <p className="opacity-80">{result.error || 'Something went wrong. Please try again.'}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 flex items-center gap-4 text-red-400">
          <AlertCircle className="h-6 w-6 shrink-0" />
          <p className="font-medium">{error}</p>
        </div>
      )}
    </div>
  )
}

export default RunAgent