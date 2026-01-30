import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useLeadStore } from '../store/leadStore'
import { ArrowLeft, ThumbsUp, ThumbsDown, ExternalLink, Building, Target, Sparkles, CheckCircle2, XCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

function LeadDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { currentLead, fetchLeadById, submitFeedback, loading } = useLeadStore()
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  useEffect(() => {
    if (id) {
      fetchLeadById(id)
    }
  }, [id, fetchLeadById])

  const handleFeedback = async (rating) => {
    try {
      await submitFeedback(currentLead.id, rating)
      setFeedbackSubmitted(true)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-screen space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-accent-indigo"></div>
        <p className="text-slate-400 animate-pulse">Analyzing evidence stream...</p>
      </div>
    )
  }

  if (!currentLead) {
    return (
      <div className="text-center py-24 px-8">
        <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10">
          <XCircle className="h-10 w-10 text-slate-600" />
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">Lead Expired or Not Found</h3>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">
          The intelligence signal you are tracking is no longer active in our primary database.
        </p>
        <button onClick={() => navigate('/leads')} className="btn-primary">
          Return to Intelligence Bank
        </button>
      </div>
    )
  }

  const getScoreStyle = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    if (score >= 60) return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20'
  }

  return (
    <div className="max-w-5xl mx-auto p-4 md:p-8 space-y-8 pb-32">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center text-slate-400 hover:text-white transition-colors group text-sm font-bold uppercase tracking-widest"
      >
        <ArrowLeft className="h-4 w-4 mr-2 group-hover:-translate-x-1 transition-transform" />
        Back to Intelligence Bank
      </button>

      <div className="glass-card overflow-hidden">
        {/* Header Section */}
        <div className="px-8 py-10 bg-white/[0.02] border-b border-white/5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-6">
              <div className="h-20 w-20 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-accent-indigo shadow-inner">
                <Building className="h-10 w-10" />
              </div>
              <div>
                <h1 className="text-4xl font-extrabold text-white tracking-tight leading-none mb-2">{currentLead.company}</h1>
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 font-bold uppercase tracking-[0.2em] text-xs">Primary Target Card</span>
                  <div className="w-1 h-1 bg-slate-700 rounded-full" />
                  <span className="text-accent-indigo font-bold text-xs uppercase tracking-widest italic">{currentLead.industry || 'Technology'}</span>
                </div>
              </div>
            </div>
            <div className={`px-6 py-3 rounded-2xl border text-center ${getScoreStyle(currentLead.score)}`}>
              <p className="text-[10px] font-bold uppercase tracking-widest opacity-60 mb-1">Quality Index</p>
              <p className="text-3xl font-black">{currentLead.score}%</p>
            </div>
          </div>
        </div>

        <div className="p-8 md:p-12">
          {/* Main Grid */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
            {/* Left Column: Data points */}
            <div className="md:col-span-4 space-y-10">
              <section>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                  <Target className="h-4 w-4" /> Attributes
                </h3>
                <dl className="space-y-6">
                  <div>
                    <dt className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-1">Market Segment</dt>
                    <dd className="text-lg font-bold text-white">{currentLead.industry || 'Inferred Sector'}</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-1">Match Confidence</dt>
                    <dd className="text-lg font-bold text-white">{Math.round(currentLead.confidence * 100)}% Verified</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] font-bold text-slate-600 uppercase tracking-widest mb-1">Source Signals</dt>
                    <dd className="text-lg font-bold text-accent-emerald">{currentLead.evidence_count || 0} Data Points</dd>
                  </div>
                  {currentLead.website_url && (
                    <div className="pt-4">
                      <a
                        href={currentLead.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white font-bold text-xs uppercase tracking-widest hover:bg-white/10 transition-all"
                      >
                        <span>Visit Domain</span>
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  )}
                </dl>
              </section>
            </div>

            {/* Right Column: Reasoning */}
            <div className="md:col-span-8 space-y-10">
              <section>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                  <Sparkles className="h-4 w-4" /> Intelligence Synopsis
                </h3>
                <div className="space-y-4">
                  {currentLead.reasons?.map((reason, index) => (
                    <div key={index} className="flex gap-4 p-5 bg-white/[0.03] border border-white/5 rounded-2xl relative group hover:border-accent-indigo/30 transition-all">
                      <div className="flex-shrink-0 w-8 h-8 bg-accent-indigo/10 text-accent-indigo rounded-lg flex items-center justify-center text-xs font-black">
                        0{index + 1}
                      </div>
                      <p className="text-slate-300 leading-relaxed italic">
                        "{reason}"
                      </p>
                    </div>
                  )) || (
                      <p className="text-slate-500 italic">Predictive analysis currently processing evidence streams...</p>
                    )}
                </div>
              </section>

              {/* Feedback Section */}
              <section className="bg-accent-indigo/5 border border-accent-indigo/10 rounded-2xl p-8">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-2">Signal Validation</h3>
                    <p className="text-sm text-slate-400 max-w-sm">
                      Validate this intelligence to refine future agent discovery algorithms.
                    </p>
                  </div>

                  {!feedbackSubmitted && !currentLead.feedback ? (
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleFeedback('good')}
                        className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-emerald-500/20 transition-all"
                      >
                        <ThumbsUp className="h-4 w-4" /> Confirm
                      </button>
                      <button
                        onClick={() => handleFeedback('bad')}
                        className="flex items-center gap-2 bg-rose-500/10 text-rose-400 border border-rose-500/20 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-rose-500/20 transition-all"
                      >
                        <ThumbsDown className="h-4 w-4" /> Reject
                      </button>
                    </div>
                  ) : (
                    <div className={`flex items-center gap-3 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest border ${currentLead.feedback?.rating === 'good' || feedbackSubmitted
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                      {currentLead.feedback?.rating === 'good' || feedbackSubmitted ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                      <span>Signal {currentLead.feedback?.rating === 'good' || feedbackSubmitted ? 'Validated' : 'Rejected'}</span>
                    </div>
                  )}
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LeadDetail