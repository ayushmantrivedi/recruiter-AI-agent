import { Link } from 'react-router-dom';
import {
  MapPin,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  Eye,
  Building
} from 'lucide-react';
import { clsx } from 'clsx';

const LeadCard = ({ lead, onFeedback }) => {
  const getScoreColor = (score) => {
    if (score >= 80) return 'bg-green-100 text-green-800 border-green-200';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-red-100 text-red-800 border-red-200';
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return 'High Priority';
    if (score >= 60) return 'Medium Priority';
    return 'Low Priority';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-12 w-12 rounded-lg bg-primary-100 flex items-center justify-center">
              <Building className="h-6 w-6 text-primary-600" />
            </div>
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-semibold text-gray-900">{lead.company}</h3>
            <p className="text-sm text-gray-600">{lead.industry || 'Technology'}</p>
          </div>
        </div>

        <div className="flex flex-col items-end space-y-2">
          <span className={clsx(
            'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border',
            getScoreColor(lead.score)
          )}>
            {lead.score}/100 - {getScoreLabel(lead.score)}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-3 mb-4">
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-1">Key Position</h4>
          <p className="text-sm text-gray-700">{lead.title || 'Various engineering roles'}</p>
        </div>

        {lead.location && (
          <div className="flex items-center text-sm text-gray-600">
            <MapPin className="h-4 w-4 mr-1" />
            {lead.location}
          </div>
        )}

        {lead.reasons && lead.reasons.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Why This Lead</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              {lead.reasons.slice(0, 3).map((reason, index) => (
                <li key={index} className="flex items-start">
                  <span className="text-primary-500 mr-2">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-3">
          <Link
            to={`/leads/${lead.id}`}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Details
          </Link>

          {lead.website_url && (
            <a
              href={lead.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Visit Site
            </a>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 mr-2">Feedback:</span>
          <button
            onClick={() => onFeedback(lead.id, 1)}
            className="p-2 text-green-600 hover:text-green-700 hover:bg-green-50 rounded-md transition-colors"
            title="Good Lead"
          >
            <ThumbsUp className="h-5 w-5" />
          </button>
          <button
            onClick={() => onFeedback(lead.id, 0)}
            className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
            title="Bad Lead"
          >
            <ThumbsDown className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Metadata */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{lead.evidence_count || 0} evidence points</span>
          <span>Last updated: {new Date(lead.last_updated || lead.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
};

export default LeadCard;
