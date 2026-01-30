import { Link } from 'react-router-dom';
import {
  MapPin,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  Eye,
  Building,
  Target,
  Clock
} from 'lucide-react';
import { clsx } from 'clsx';

const LeadCard = ({ lead, onFeedback }) => {
  const getScoreStyle = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 60) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'Strategic Priority';
    if (score >= 60) return 'Qualified Lead';
    return 'Secondary Target';
  };

  return (
    <div className="glass-card p-6 group hover:border-accent-indigo/40 transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-14 w-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-accent-indigo shadow-inner">
              <Building className="h-8 w-8" />
            </div>
          </div>
          <div className="ml-4">
            <h3 className="text-xl font-bold text-white group-hover:text-accent-indigo transition-colors">{lead.company}</h3>
            <p className="text-sm text-slate-500 font-medium uppercase tracking-widest">{lead.industry || 'Technology'}</p>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <span className={clsx(
          'inline-flex items-center px-4 py-1.5 rounded-xl text-xs font-bold border uppercase tracking-widest leading-none',
          getScoreStyle(lead.score)
        )}>
          <Target className="h-3 w-3 mr-2" />
          {lead.score}% Match • {getScoreLabel(lead.score)}
        </span>
      </div>

      {/* Content */}
      <div className="space-y-4 mb-8">
        <div>
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Prime Focus</h4>
          <p className="text-slate-200 text-lg font-medium">{lead.title || 'Inferred engineering demand'}</p>
        </div>

        {lead.location && (
          <div className="flex items-center text-sm text-slate-400 font-medium">
            <MapPin className="h-4 w-4 mr-2 text-indigo-400" />
            {lead.location}
          </div>
        )}

        {lead.reasons && lead.reasons.length > 0 && (
          <div className="bg-black/20 p-4 rounded-2xl border border-white/5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Intelligence Signals</h4>
            <ul className="text-sm text-slate-400 space-y-2">
              {lead.reasons.slice(0, 2).map((reason, index) => (
                <li key={index} className="flex items-start italic leading-relaxed">
                  <span className="text-accent-indigo mr-2 text-lg">“</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-6 border-t border-white/5">
        <div className="flex items-center gap-3">
          <Link
            to={`/leads/${lead.id}`}
            className="p-3 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all"
            title="Evidence Details"
          >
            <Eye className="h-5 w-5" />
          </Link>

          {lead.website_url && (
            <a
              href={lead.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-3 bg-white/5 border border-white/10 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-all"
              title="Visit Domain"
            >
              <ExternalLink className="h-5 w-5" />
            </a>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onFeedback(lead.id, 1)}
            className="p-3 text-slate-600 hover:text-emerald-400 hover:shadow-lg hover:shadow-emerald-500/10 transition-all"
            title="Verify Signal"
          >
            <ThumbsUp className="h-5 w-5" />
          </button>
          <button
            onClick={() => onFeedback(lead.id, 0)}
            className="p-3 text-slate-600 hover:text-rose-400 hover:shadow-lg hover:shadow-rose-500/10 transition-all"
            title="Reject Signal"
          >
            <ThumbsDown className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-6 flex items-center justify-between text-[10px] font-bold text-slate-600 uppercase tracking-[0.2em]">
        <span className="flex items-center gap-1.5">
          <Target className="h-3 w-3" />
          {lead.evidence_count || 0} Data Points
        </span>
        <span className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          {new Date(lead.last_updated || lead.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
};

export default LeadCard;
