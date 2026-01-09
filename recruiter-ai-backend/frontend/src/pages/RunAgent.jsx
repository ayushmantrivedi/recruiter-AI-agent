import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLeadStore } from '../store/leadStore'
import { Play, Loader, CheckCircle, AlertCircle } from 'lucide-react'

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

      // If it's not completed immediately, poll for status
      if (response.status !== 'completed') {
        pollQueryStatus(response.query_id)
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
    }, 2000) // Poll every 2 seconds

    // Stop polling after 2 minutes
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
    "Find CTO candidates for fintech startups"
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Run AI Agent</h1>
        <p className="mt-2 text-gray-600">
          Enter a natural language query to discover hiring leads using our AI agents.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Your Query
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Find senior backend engineers in Bangalore with 5+ years experience"
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isRunning || !query.trim()}
            className="flex items-center space-x-2 bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <Loader className="h-5 w-5 animate-spin" />
                <span>Running Agent...</span>
              </>
            ) : (
              <>
                <Play className="h-5 w-5" />
                <span>Run Agent</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Example Queries */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Example Queries</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => setQuery(example)}
              className="text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 hover:border-primary-300 transition-colors"
            >
              <p className="text-sm text-gray-700">{example}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center space-x-3 mb-4">
            {result.status === 'completed' ? (
              <CheckCircle className="h-6 w-6 text-green-600" />
            ) : result.status === 'failed' ? (
              <AlertCircle className="h-6 w-6 text-red-600" />
            ) : (
              <Loader className="h-6 w-6 text-blue-600 animate-spin" />
            )}
            <h2 className="text-lg font-medium text-gray-900">
              Query Results
            </h2>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-500">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                  result.status === 'completed'
                    ? 'bg-green-100 text-green-800'
                    : result.status === 'failed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-blue-100 text-blue-800'
                }`}>
                  {result.status}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-500">Query ID:</span>
                <span className="ml-2 text-gray-900">{result.query_id}</span>
              </div>
              <div>
                <span className="font-medium text-gray-500">Leads Found:</span>
                <span className="ml-2 text-gray-900">
                  {result.leads ? result.leads.length : 0}
                </span>
              </div>
            </div>

            {result.status === 'completed' && result.leads && result.leads.length > 0 && (
              <div className="border-t pt-4">
                <h3 className="text-md font-medium text-gray-900 mb-3">
                  Top Leads Found
                </h3>
                <div className="space-y-3">
                  {result.leads.slice(0, 3).map((lead, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{lead.company}</p>
                        <p className="text-sm text-gray-600">
                          Score: {lead.score}/100 • {lead.reasons?.[0] || 'No reason provided'}
                        </p>
                      </div>
                      <button
                        onClick={() => navigate(`/leads/${lead.id || lead.company}`)}
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        View Details →
                      </button>
                    </div>
                  ))}
                </div>
                {result.leads.length > 3 && (
                  <p className="text-sm text-gray-600 mt-3">
                    And {result.leads.length - 3} more leads found...
                  </p>
                )}
              </div>
            )}

            {result.status === 'failed' && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-800">
                  Query failed: {result.error || 'Unknown error occurred'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-red-800">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default RunAgent