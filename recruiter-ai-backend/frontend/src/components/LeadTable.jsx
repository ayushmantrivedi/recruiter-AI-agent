import { Link } from 'react-router-dom'
import { Eye, ThumbsUp, ThumbsDown } from 'lucide-react'
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

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  if (!leads || leads.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No leads found. Run an agent query to discover leads.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Company
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Score
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Confidence
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Reasons
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {leads.map((lead) => (
            <tr key={lead.id || lead.company} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">
                  {lead.company}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getScoreColor(lead.score)}`}>
                  {lead.score}/100
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {Math.round(lead.confidence * 100)}%
              </td>
              <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                {lead.reasons?.slice(0, 2).join(', ') || 'No reasons provided'}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                <Link
                  to={`/leads/${lead.id || lead.company}`}
                  className="text-primary-600 hover:text-primary-900 inline-flex items-center"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  View
                </Link>

                {!lead.feedback && (
                  <div className="inline-flex space-x-1 ml-4">
                    <button
                      onClick={() => handleFeedback(lead.id || lead.company, 'good')}
                      className="text-green-600 hover:text-green-900"
                      title="Good lead"
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleFeedback(lead.id || lead.company, 'bad')}
                      className="text-red-600 hover:text-red-900"
                      title="Bad lead"
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </button>
                  </div>
                )}

                {lead.feedback && (
                  <span className={`text-xs px-2 py-1 rounded ${
                    lead.feedback.rating === 'good'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {lead.feedback.rating === 'good' ? '👍' : '👎'}
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default LeadTable