import { useState } from 'react';
import { Search, Play, Lightbulb } from 'lucide-react';

const RunAgentForm = ({ onSubmit, isLoading, error }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  const exampleQueries = [
    "Senior backend engineers with Python experience in fintech",
    "Frontend developers specializing in React and TypeScript",
    "Data scientists with machine learning expertise",
    "DevOps engineers with AWS and Kubernetes experience",
    "Full-stack developers with Node.js and React skills",
    "Mobile app developers (iOS/Android) for growing startups"
  ];

  return (
    <div className="space-y-6">
      {/* Main Form */}
      <div className="card">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Describe Your Ideal Candidate
          </h2>
          <p className="text-gray-600">
            Be specific about role, skills, experience level, and company preferences for the best results.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Search Query
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <textarea
                id="query"
                rows={4}
                className="input pl-10 resize-none"
                placeholder="e.g., Senior backend engineers with 5+ years Python experience in fintech companies, remote work preferred"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-danger-50 p-4">
              <div className="text-sm text-danger-700">{error}</div>
            </div>
          )}

          <div className="flex justify-center">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="btn-primary flex items-center text-lg px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Play className="h-5 w-5 mr-2" />
              {isLoading ? 'Running AI Agent...' : 'Run AI Agent'}
            </button>
          </div>
        </form>
      </div>

      {/* Example Queries */}
      <div className="card">
        <div className="flex items-center mb-4">
          <Lightbulb className="h-5 w-5 text-yellow-500 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">Example Queries</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exampleQueries.map((example, index) => (
            <button
              key={index}
              onClick={() => setQuery(example)}
              disabled={isLoading}
              className="text-left p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <p className="text-sm text-gray-700 font-medium mb-1">
                {example.split(' ').slice(0, 3).join(' ')}...
              </p>
              <p className="text-xs text-gray-600">{example}</p>
            </button>
          ))}
        </div>

        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Tips for Better Results:</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Include specific technologies (Python, React, AWS, etc.)</li>
            <li>• Mention experience level (Senior, Junior, Mid-level)</li>
            <li>• Specify location preferences (Remote, San Francisco, etc.)</li>
            <li>• Note industry focus (Fintech, Healthcare, E-commerce)</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RunAgentForm;
