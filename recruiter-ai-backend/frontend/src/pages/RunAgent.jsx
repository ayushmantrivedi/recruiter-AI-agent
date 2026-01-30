import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLeadStore } from '../store/leadStore'
import { Play, Loader, CheckCircle, AlertCircle, Sparkles, ChevronRight } from 'lucide-react'

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
      setError(err.message || 'Failed to run agent query')
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
        setError('Failed to check query status')
      }
    }, 2000)

    setTimeout(() => {
      clearInterval(pollInterval)
      setIsRunning(false)
    }, 120000)
  }

  const exampleQueries = [
    "Find senior backend engineers in Bangalore",
    "Remote frontend developers with React experience",
    "Data scientists for machine learning roles",
    "DevOps engineers for cloud infrastructure",
  ]

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-8 pb-32">
      <header className="mb-10 text-center md:text-left">
        <h1 className="text-4xl font-bold text-white tracking-tight flex items-center justify-center md:justify-start gap-4">
          <div className="bg-accent-indigo p-2 rounded-xl shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          Discovery Agent
        </h1>
        <p className="mt-4 text-slate-400 text-lg max-w-2xl">
          Deploy AI agents to scan the global market and identify high-value candidates through natural language intelligence.
        </p>
      </header>

      <section className="glass-card p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="query" className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
              Strategic Intent
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Identify senior React developers in London with deep FinTech experience..."
              className="w-full h-32 input-field resize-none text-lg"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isRunning || !query.trim()}
            className="btn-primary w-full md:w-auto flex items-center justify-center space-x-3"
          >
            {isRunning ? (
              <>
                <Loader className="h-5 w-5 animate-spin" />
                <span>Scanning Market...</span>
              </>
            ) : (
              <>
                <Play className="h-5 w-5 fill-current" />
                <span>Execute Mission</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-white/5">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Tactical Examples</p>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                className="px-4 py-2 bg-white/5 border border-white/5 rounded-full text-sm text-slate-400 hover:bg-white/10 hover:text-white transition-all"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Results Container - Scrollable only if needed */}
      {result && (
        <div className="glass-card overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
            <div className="flex items-center space-x-4">
              <div className={`p-2 rounded-lg ${result.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                  result.status === 'failed' ? 'bg-red-500/20 text-red-400' : 'bg-indigo-500/20 text-indigo-400'
                }`}>
                {result.status === 'completed' ? <CheckCircle className="h-6 w-6" /> :
                  result.status === 'failed' ? <AlertCircle className="h-6 w-6" /> : <Loader className="h-6 w-6 animate-spin" />}
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Analysis Findings</h2>
                <p className="text-sm text-slate-500 uppercase tracking-tighter">Query ID: {result.query_id.slice(0, 8)}...</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-white">{result.leads ? result.leads.length : 0}</p>
              <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">Leads Detected</p>
            </div>
          </div>

          <div className="p-8 space-y-8 max-h-[600px] overflow-y-auto">
            {/* Synthesis Report Integration */}
            {result.synthesis_report && (
              <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-2xl p-6 relative">
                <div className="absolute top-4 right-4 text-indigo-400 opacity-20"><Sparkles className="h-12 w-12" /></div>
                <h3 className="text-indigo-400 text-xs font-bold uppercase tracking-widest mb-4">Strategic Summary</h3>
                <div className="text-slate-300 leading-relaxed text-lg prose prose-invert max-w-none">
                  {result.synthesis_report.split('\n').map((line, i) => (
                    <p key={i} className="mb-2">{line.startsWith('#') ? <strong>{line.replace(/#/g, '')}</strong> : line}</p>
                  ))}
                </div>
              </div>
            )}

            {result.status === 'completed' && result.leads && result.leads.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-white font-bold text-lg mb-4 flex items-center gap-2">
                  Verified Candidates
                  <span className="text-slate-500 text-sm font-normal">({result.leads.length})</span>
                </h3>
                <div className="grid grid-cols-1 gap-4">
                  {result.leads.map((lead, index) => (
                    <div key={index} className="flex items-center justify-between p-6 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/[0.08] hover:border-indigo-500/30 transition-all group">
                      <div className="space-y-1">
                        <p className="font-bold text-white text-lg">{lead.company}</p>
                        <p className="text-slate-400 flex items-center gap-3">
                          <span className="bg-indigo-500/20 text-indigo-400 text-xs font-bold px-2 py-0.5 rounded">FIT: {lead.score}%</span>
                          <span className="truncate max-w-sm italic opacity-60">"{lead.reasons?.[0]}"</span>
                        </p>
                      </div>
                      <button
                        onClick={() => navigate(`/leads/${lead.id || lead.company}`)}
                        className="p-3 bg-white/5 rounded-xl group-hover:bg-indigo-500 group-hover:text-white transition-all"
                      >
                        <ChevronRight className="h-5 w-5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.status === 'failed' && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-red-400">
                <p className="font-bold mb-2">Operation Aborted</p>
                <p className="opacity-80">{result.error || 'A critical error occurred during the market scan.'}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 flex items-center gap-4 text-red-400 animate-in shake duration-300">
          <AlertCircle className="h-6 w-6 shrink-0" />
          <p className="font-medium">{error}</p>
        </div>
      )}
    </div>
  )
}

export default RunAgent