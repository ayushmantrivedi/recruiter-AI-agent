import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Zap, User, ArrowRight, Sparkles, Loader2 } from 'lucide-react'
import { useAuthStore } from '../store/authStore'

function Login() {
  const [identity, setIdentity] = useState('')
  const { loginByIdentity, loading, error } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await loginByIdentity(identity)
    if (result.success) {
      navigate('/')
      window.location.reload()
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated Background Orbs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent-coral/10 rounded-full blur-3xl animate-float"
          style={{ animationDelay: '0s' }} />
        <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-accent-teal/8 rounded-full blur-3xl animate-float"
          style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-accent-purple/6 rounded-full blur-3xl animate-float"
          style={{ animationDelay: '4s' }} />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-accent-coral to-primary-600 rounded-2xl mb-6 shadow-lg shadow-accent-coral/30">
            <Zap className="h-8 w-8 text-white" stroke-width={2.5} />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Talent<span className="text-accent-coral">Scout</span>
          </h1>
          <p className="text-slate-500 font-medium">
            Find your next great hire, faster
          </p>
        </div>

        {/* Login Card */}
        <div className="glass-card p-8 glow-border">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Welcome back</h2>
            <p className="text-slate-400">
              Sign in to continue your recruiting journey
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-slate-300 ml-1">
                Your ID or Username
              </label>
              <div className="relative group">
                <User className="h-5 w-5 text-slate-500 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-coral transition-colors" />
                <input
                  type="text"
                  value={identity}
                  onChange={(e) => setIdentity(e.target.value)}
                  placeholder="Enter your ID or username"
                  className="input-field w-full pl-12"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex items-center justify-center gap-2.5">
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Signing you in...</span>
                  </>
                ) : (
                  <>
                    <span>Get Started</span>
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-0.5 transition-transform" />
                  </>
                )}
              </div>
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-700/50">
            <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
              <Sparkles className="h-4 w-4 text-accent-teal" />
              <span>No password needed • Secure access</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-sm text-slate-500">
            First time here?{' '}
            <span className="text-accent-coral font-semibold cursor-pointer hover:underline">
              Learn more
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
