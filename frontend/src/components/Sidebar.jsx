import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Play,
  Target,
  BarChart3,
  FileText,
  ShieldCheck
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Terminal', href: '/', icon: LayoutDashboard },
  { name: 'Discovery', href: '/run-agent', icon: Play },
  { name: 'Intelligence', href: '/leads', icon: Target },
  { name: 'Analytics', href: '/metrics', icon: BarChart3 },
]

function Sidebar() {
  const location = useLocation()

  return (
    <div className="w-64 bg-bg-sidebar backdrop-blur-glass border-r border-white/5 h-screen flex flex-col pt-8">
      <div className="px-6 mb-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent-indigo rounded-xl flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <span className="font-heading font-bold text-xl text-white tracking-tight">Recruiter<span className="text-accent-indigo">AI</span></span>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={clsx(
                'flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-bold uppercase tracking-widest transition-all duration-200',
                isActive
                  ? 'bg-accent-indigo text-white shadow-lg shadow-indigo-500/10'
                  : 'text-slate-500 hover:text-white hover:bg-white/5'
              )}
            >
              <item.icon className={clsx("h-5 w-5", isActive ? "text-white" : "text-slate-500")} />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-white/5">
        <div className="bg-white/5 rounded-2xl p-4">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">System Status</p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-accent-emerald rounded-full animate-pulse" />
            <span className="text-xs font-bold text-slate-300">Agents Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar