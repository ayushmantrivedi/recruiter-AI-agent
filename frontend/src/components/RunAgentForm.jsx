import { useState } from 'react';
import { Search, Play, Lightbulb, Sparkles, Zap, Globe, Cpu } from 'lucide-react';

const RunAgentForm = ({ onSubmit, isLoading, error }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  const exampleQueries = [
    { title: "Backend Scalability", text: "Senior backend engineers with Python experience in high-growth fintech", icon: <Cpu className="h-4 w-4" /> },
    { title: "Frontend Architecture", text: "Frontend architects specializing in React and performance optimization", icon: <Zap className="h-4 w-4" /> },
    { title: "Intelligence & ML", text: "Data scientists with LLM and production machine learning expertise", icon: <Sparkles className="h-4 w-4" /> },
    { title: "Global Infrastructure", text: "Site reliability engineers with multi-cloud and Kubernetes mastery", icon: <Globe className="h-4 w-4" /> }
  ];

  return (
    <div className="space-y-8">
      {/* Main Form */}
      <div className="glass-card p-8 md:p-12 relative overflow-hidden group">
        {/* Subtle decorative elements */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-accent-indigo/5 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl pointer-events-none" />

        <div className="relative mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-accent-indigo/10 rounded-lg text-accent-indigo">
              <Sparkles className="h-5 w-5" />
            </div>
            <h2 className="text-2xl font-black text-white uppercase tracking-tight">
              Objective Specification
            </h2>
          </div>
          <p className="text-slate-400 text-lg max-w-2xl leading-relaxed">
            Specify the role architecture, core competencies, and strategic context for your AI agent to begin scouting.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8 relative">
          <div>
            <div className="flex justify-between items-end mb-3">
              <label htmlFor="query" className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">
                Command Prompt
              </label>
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest italic">Natural Language Interface</span>
            </div>
            <div className="relative group/input">
              <div className="absolute top-6 left-6 pointer-events-none">
                <Search className="h-6 w-6 text-slate-500 group-focus-within/input:text-accent-indigo transition-colors" />
              </div>
              <textarea
                id="query"
                rows={5}
                className="input-field pl-16 py-6 text-lg"
                placeholder="e.g., Deploy a senior infrastructure engineer specialized in AWS and Rust for a Series B healthcare startup, European timezone focus..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
          </div>

          {error && (
            <div className="glass-card p-4 border-rose-500/20 bg-rose-500/5">
              <div className="text-sm font-bold text-rose-400 flex items-center gap-2">
                <Zap className="h-4 w-4" />
                {error}
              </div>
            </div>
          )}

          <div className="flex justify-center">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="btn-primary group/btn min-w-[240px] py-4 text-xl"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                  Neural Processing...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 mr-3 group-hover:translate-x-1 transition-transform" />
                  Execute Deployment
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Example Queries */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
        <div className="glass-card p-8">
          <div className="flex items-center gap-3 mb-8">
            <Lightbulb className="h-5 w-5 text-amber-400 shadow-sm" />
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em]">Intelligence Templates</h3>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {exampleQueries.map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example.text)}
                disabled={isLoading}
                className="text-left p-5 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-accent-indigo/30 hover:bg-white/[0.04] transition-all group/example disabled:opacity-50"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-1.5 bg-slate-800 rounded-lg text-slate-500 group-hover/example:text-accent-indigo transition-colors">
                    {example.icon}
                  </div>
                  <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">{example.title}</p>
                </div>
                <p className="text-sm text-slate-300 italic group-hover/example:text-white transition-colors">"{example.text}"</p>
              </button>
            ))}
          </div>
        </div>

        <div className="glass-card p-10 flex flex-col justify-center bg-accent-indigo/[0.02]">
          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-accent-indigo" /> Parameter Guidance
          </h4>
          <ul className="space-y-6">
            {[
              { label: "Technical Stack", text: "Enforce specific requirements like 'Golang', 'Kubernetes', or 'Solidity'." },
              { label: "Experience Seniority", text: "Define the strategic level: 'Founding Engineer', 'Staff', or 'Tech Lead'." },
              { label: "Market Context", text: "Focus on sector specifics like 'Series A FinTech' or 'Privacy-focused Labs'." },
              { label: "Operational Model", text: "Specify 'Full-Remote', 'Hybrid NYC', or 'Async-first' preferences." }
            ].map((tip, i) => (
              <li key={i} className="flex gap-4">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-indigo mt-1.5" />
                <div>
                  <p className="text-xs font-bold text-slate-200 uppercase tracking-widest mb-1">{tip.label}</p>
                  <p className="text-sm text-slate-500 leading-relaxed font-medium">{tip.text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RunAgentForm;
