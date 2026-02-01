import { useNavigate } from "react-router-dom"
import { Play, Users, TrendingUp, LogOut, Sparkles, ArrowRight } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

function Dashboard() {
  const recruiterId = localStorage.getItem("recruiter_id")
  const navigate = useNavigate()
  const { logout, user } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const cards = [
    {
      title: 'Find Talent',
      desc: 'Search for candidates using natural language',
      icon: <Play className="h-6 w-6" />,
      path: '/run-agent',
      gradient: 'from-accent-coral to-primary-600',
      iconBg: 'bg-accent-coral/20',
      textColor: 'text-accent-coral'
    },
    {
      title: 'Your Leads',
      desc: 'Review and manage discovered candidates',
      icon: <Users className="h-6 w-6" />,
      path: '/leads',
      gradient: 'from-accent-teal to-teal-600',
      iconBg: 'bg-accent-teal/20',
      textColor: 'text-accent-teal'
    },
    {
      title: 'Insights',
      desc: 'Track trends and analyze your recruiting data',
      icon: <TrendingUp className="h-6 w-6" />,
      path: '/metrics',
      gradient: 'from-accent-purple to-purple-600',
      iconBg: 'bg-accent-purple/20',
      textColor: 'text-accent-purple'
    },
  ]

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="mb-12 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl md:text-5xl font-bold text-white">
              Welcome back{recruiterId ? `, ${recruiterId}` : ''}
            </h1>
            <Sparkles className="h-6 w-6 text-accent-coral animate-pulse-soft" />
          </div>
          <p className="text-slate-400 text-lg">
            Ready to find amazing talent today?
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="btn-secondary flex items-center gap-2 self-start md:self-auto"
        >
          <LogOut className="h-4 w-4" />
          <span>Sign Out</span>
        </button>
      </header>

      {/* Main Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {cards.map((card, i) => (
          <div
            key={i}
            onClick={() => navigate(card.path)}
            className="glass-card p-8 group cursor-pointer hover-lift glow-border"
          >
            <div className={`inline-flex p-4 ${card.iconBg} ${card.textColor} rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300`}>
              {card.icon}
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">{card.title}</h3>
            <p className="text-slate-400 leading-relaxed mb-6">{card.desc}</p>
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-400 group-hover:text-accent-coral transition-colors">
              <span>Get started</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        ))}
      </div>

      {/* Quick Search Section */}
      <section className="glass-card p-8 glow-border">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Quick Search</h2>
            <p className="text-slate-400">
              Describe who you're looking for and let AI do the rest
            </p>
          </div>
        </div>

        <div
          onClick={() => navigate('/run-agent')}
          className="group cursor-pointer bg-gradient-to-r from-slate-900/60 to-slate-800/40 border border-slate-700/50 rounded-2xl p-6 hover:border-accent-coral/50 transition-all duration-300"
        >
          <div className="flex items-center justify-between">
            <p className="text-slate-500 group-hover:text-slate-400 transition-colors">
              Try "Find senior React developers in San Francisco..."
            </p>
            <div className="p-3 bg-accent-coral/10 text-accent-coral rounded-xl opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowRight className="h-5 w-5" />
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar (Optional - can add real stats later) */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-slate-900/60 to-slate-800/40 border border-slate-700/50 rounded-2xl p-6">
          <p className="text-sm text-slate-500 mb-2 font-semibold">Total Searches</p>
          <p className="text-3xl font-bold text-white">—</p>
        </div>
        <div className="bg-gradient-to-br from-slate-900/60 to-slate-800/40 border border-slate-700/50 rounded-2xl p-6">
          <p className="text-sm text-slate-500 mb-2 font-semibold">Leads Found</p>
          <p className="text-3xl font-bold text-white">—</p>
        </div>
        <div className="bg-gradient-to-br from-slate-900/60 to-slate-800/40 border border-slate-700/50 rounded-2xl p-6">
          <p className="text-sm text-slate-500 mb-2 font-semibold">Success Rate</p>
          <p className="text-3xl font-bold text-white">—</p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
