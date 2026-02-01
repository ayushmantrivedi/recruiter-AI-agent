import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { LogOut, User, Bell, Search, Settings } from 'lucide-react'

function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="bg-bg-sidebar/40 backdrop-blur-glass border-b border-white/5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          <div className="flex items-center">
            <div className="relative group">
              <Search className="h-5 w-5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 group-hover:text-accent-indigo transition-colors" />
              <input
                type="text"
                placeholder="Search intelligence records..."
                className="bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-accent-indigo/50 w-64 transition-all focus:w-80"
              />
            </div>
          </div>

          <div className="flex items-center gap-6">
            <button className="p-2.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-xl transition-all relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-accent-indigo rounded-full border-2 border-[#0f172a]" />
            </button>
            <button className="p-2.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-xl transition-all">
              <Settings className="h-5 w-5" />
            </button>

            <div className="w-px h-8 bg-white/10 mx-2" />

            <div className="flex items-center gap-4">
              <div className="flex flex-col items-end hidden sm:block">
                <span className="text-sm font-bold text-white leading-none mb-1">
                  {user?.full_name || user?.email}
                </span>
                <span className="text-[10px] font-bold text-accent-indigo uppercase tracking-widest leading-none">
                  {user?.company || 'Recruiter Pro'}
                </span>
              </div>
              <div className="h-10 w-10 rounded-xl bg-accent-indigo/20 border border-accent-indigo/30 flex items-center justify-center text-accent-indigo shadow-inner overflow-hidden">
                {user?.profile_pic ? (
                  <img src={user.profile_pic} alt="Profile" className="h-full w-full object-cover" />
                ) : (
                  <User className="h-6 w-6" />
                )}
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all font-bold text-xs uppercase tracking-widest"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden md:block">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar