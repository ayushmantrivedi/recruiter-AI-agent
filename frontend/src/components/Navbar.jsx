import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { LogOut, User, Zap } from 'lucide-react'

function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="sticky top-0 z-50 bg-bg-sidebar/90 backdrop-blur-glass border-b border-slate-700/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div
            onClick={() => navigate('/')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="p-2 bg-gradient-to-br from-accent-coral to-primary-600 rounded-xl shadow-lg shadow-accent-coral/20 group-hover:scale-105 transition-transform">
              <Zap className="h-6 w-6 text-white" stroke-width={2.5} />
            </div>
            <span className="text-xl font-bold text-white">
              Talent<span className="text-accent-coral">Scout</span>
            </span>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-6">
            {/* User Info */}
            <div className="hidden sm:flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center text-accent-coral">
                {user?.profile_pic ? (
                  <img src={user.profile_pic} alt="Profile" className="h-full w-full object-cover rounded-xl" />
                ) : (
                  <User className="h-5 w-5" />
                )}
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-white leading-tight">
                  {user?.full_name || user?.email || 'Recruiter'}
                </span>
                <span className="text-xs text-slate-500 leading-tight">
                  {user?.company || 'TalentScout'}
                </span>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="btn-secondary flex items-center gap-2 hover:text-red-400 hover:border-red-500/30"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden md:block">Sign Out</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar