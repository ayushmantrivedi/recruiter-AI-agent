import { useNavigate } from "react-router-dom"
import { Play, Grid, BarChart3, LogOut, Search } from 'lucide-react'

function Dashboard() {
  const recruiterId = localStorage.getItem("recruiter_id")
  const navigate = useNavigate()

  const logout = () => {
    localStorage.removeItem("recruiter_id")
    window.location.href = "/login"
  }

  const cards = [
    { title: 'Run AI Agent', desc: 'Find top talent with natural language', icon: <Play className="h-6 w-6" />, path: '/run-agent', color: 'bg-indigo-500' },
    { title: 'View Leads', desc: 'Manage your discovered candidates', icon: <Grid className="h-6 w-6" />, path: '/leads', color: 'bg-emerald-500' },
    { title: 'Market Insights', desc: 'Analyze talent trends and metrics', icon: <BarChart3 className="h-6 w-6" />, path: '/metrics', color: 'bg-amber-500' },
  ]

  return (
    <div className="min-h-screen p-8 max-w-6xl mx-auto">
      <header className="flex justify-between items-center mb-12">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-white mb-2">
            Welcome back, <span className="text-accent-indigo">{recruiterId}</span>
          </h1>
          <p className="text-slate-400 text-lg">Platform Overview & Command Center</p>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-all"
        >
          <LogOut className="h-4 w-4" />
          <span>Logout</span>
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {cards.map((card, i) => (
          <div
            key={i}
            onClick={() => navigate(card.path)}
            className="glass-card p-8 group cursor-pointer hover:border-indigo-500/50 transition-all duration-300"
          >
            <div className={`w-12 h-12 ${card.color} rounded-xl flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform`}>
              {card.icon}
            </div>
            <h3 className="text-xl font-bold text-white mb-2">{card.title}</h3>
            <p className="text-slate-400 leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>

      <section className="glass-card p-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-10 h-10 bg-white/5 rounded-lg flex items-center justify-center text-indigo-400">
            <Search className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Quick Start Search</h2>
            <p className="text-slate-400 text-sm">Jump straight into a talent discovery loop</p>
          </div>
        </div>

        <div
          onClick={() => navigate('/run-agent')}
          className="w-full bg-black/20 border border-white/5 rounded-2xl p-6 text-slate-500 hover:border-indigo-500/30 cursor-pointer transition-all"
        >
          Describe your ideal candidate here... (e.g. "Senior React Dev in Berlin")
        </div>
      </section>
    </div>
  )
}

export default Dashboard
