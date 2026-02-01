import { Link } from 'react-router-dom'
import { Eye, ThumbsUp, ThumbsDown, CheckCircle, XCircle } from 'lucide-react'
import { useLeadStore } from '../store/leadStore'

function LeadTable({ leads }) {
  const { submitFeedback } = useLeadStore()

  const handleFeedback = async (leadId, rating) => {
    try {
      await submitFeedback(leadId, rating)
    } catch (error) {
      console.error('Failed to submit feedback:', error)
    }
  }

  const getScoreStyle = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
    if (score >= 60) return 'text-amber-400 bg-amber-500/10 border-amber-500/20'
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20'
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="text-center py-24">
        <p className="text-slate-500 text-lg">Inventory currently empty. Deploy agents to begin discovery.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-white/5">
        <thead className="bg-white/[0.02]">
          <tr>
            <th className="px-6 py-5 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">
              Strategic Target
            </th>
            <th className="px-6 py-5 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">
              Quality Score
            </th>
            <th className="px-6 py-5 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">
              Confidence
            </th>
            <th className="px-6 py-5 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">
              Primary Signal
            </th>
            <th className="px-6 py-5 text-left text-xs font-bold text-slate-500 uppercase tracking-widest">
              Intelligence
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {leads.map((lead) => (
            <tr key={lead.id || lead.company} className="hover:bg-white/[0.04] transition-colors group">
              <td className="px-6 py-5 whitespace-nowrap">
                <div className="text-base font-bold text-white group-hover:text-accent-indigo transition-colors mt-1">
                  {lead.company}
                </div>
              </td>
              <td className="px-6 py-5 whitespace-nowrap">
                <span className={`inline-flex px-3 py-1 text-xs font-bold rounded-lg border ${getScoreStyle(lead.score)}`}>
                  {lead.score}%
                </span>
              </td>
              <td className="px-6 py-5 whitespace-nowrap text-sm text-slate-400 font-medium">
                {Math.round(lead.confidence * 100)}%
              </td>
              <td className="px-6 py-5 text-sm text-slate-400 max-w-xs truncate italic">
                "{lead.reasons?.[0] || 'Analyzing...'}"
              </td>
              <td className="px-6 py-5 whitespace-nowrap text-sm font-medium">
                <div className="flex items-center gap-4">
                  <Link
                    to={`/leads/${lead.id || lead.company}`}
                    className="p-2 bg-white/5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                  >
                    <Eye className="h-4 w-4" />
                  </Link>

                  {!lead.feedback && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleFeedback(lead.id || lead.company, 'good')}
                        className="p-2 bg-white/5 rounded-lg text-slate-600 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
                        title="Good lead"
                      >
                        <ThumbsUp className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleFeedback(lead.id || lead.company, 'bad')}
                        className="p-2 bg-white/5 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                        title="Bad lead"
                      >
                        <ThumbsDown className="h-4 w-4" />
                      </button>
                    </div>
                  )}

                  {lead.feedback && (
                    <div className={`p-2 rounded-lg ${lead.feedback.rating === 'good' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                      }`}>
                      {lead.feedback.rating === 'good' ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default LeadTable