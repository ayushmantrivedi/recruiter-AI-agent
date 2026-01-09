import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useLeadStore } from '../store/leadStore'
import { ArrowLeft, ThumbsUp, ThumbsDown, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

function LeadDetail() {
  const { id } = useParams()
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
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!currentLead) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Lead not found.</p>
        <Link to="/" className="text-primary-600 hover:text-primary-500 mt-4 inline-block">
          ← Back to Dashboard
        </Link>
      </div>
    )
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center space-x-4">
        <Link
          to="/"
          className="flex items-center text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Back to Dashboard
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">{currentLead.company}</h1>
            <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${getScoreColor(currentLead.score)}`}>
              {currentLead.score}/100 Score
            </span>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Lead Information</h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Company</dt>
                  <dd className="text-sm text-gray-900">{currentLead.company}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Score</dt>
                  <dd className="text-sm text-gray-900">{currentLead.score}/100</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Confidence</dt>
                  <dd className="text-sm text-gray-900">{Math.round(currentLead.confidence * 100)}%</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Evidence Count</dt>
                  <dd className="text-sm text-gray-900">{currentLead.evidence_count || 0}</dd>
                </div>
              </dl>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Why This Lead?</h3>
              <ul className="space-y-2">
                {currentLead.reasons?.map((reason, index) => (
                  <li key={index} className="flex items-start">
                    <span className="flex-shrink-0 w-5 h-5 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-xs font-medium mr-3 mt-0.5">
                      {index + 1}
                    </span>
                    <span className="text-sm text-gray-700">{reason}</span>
                  </li>
                )) || (
                  <li className="text-sm text-gray-500">No specific reasons provided</li>
                )}
              </ul>
            </div>
          </div>

          {/* Feedback Section */}
          {!feedbackSubmitted && !currentLead.feedback && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Provide Feedback</h3>
              <p className="text-sm text-gray-600 mb-4">
                Help improve our AI by rating this lead's quality.
              </p>
              <div className="flex space-x-4">
                <button
                  onClick={() => handleFeedback('good')}
                  className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
                >
                  <ThumbsUp className="h-5 w-5" />
                  <span>Good Lead</span>
                </button>
                <button
                  onClick={() => handleFeedback('bad')}
                  className="flex items-center space-x-2 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
                >
                  <ThumbsDown className="h-5 w-5" />
                  <span>Bad Lead</span>
                </button>
              </div>
            </div>
          )}

          {(feedbackSubmitted || currentLead.feedback) && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-2">Your Feedback</h3>
              <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${
                currentLead.feedback?.rating === 'good' || feedbackSubmitted
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {currentLead.feedback?.rating === 'good' || feedbackSubmitted ? (
                  <>
                    <ThumbsUp className="h-4 w-4" />
                    <span>Good Lead</span>
                  </>
                ) : (
                  <>
                    <ThumbsDown className="h-4 w-4" />
                    <span>Bad Lead</span>
                  </>
                )}
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Thank you for your feedback! This helps improve future recommendations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default LeadDetail