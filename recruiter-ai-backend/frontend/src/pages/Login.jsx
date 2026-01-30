import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ShieldCheck, User, ArrowRight, Sparkles, Loader2 } from 'lucide-react'
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
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#0a0f1d] relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent-indigo/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-emerald/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo Section */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 bg-accent-indigo rounded-2xl flex items-center justify-center text-white shadow-2xl shadow-indigo-500/40 mb-6">
            <ShieldCheck className="h-10 w-10" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter uppercase">
            Recruiter<span className="text-accent-indigo">AI</span>
          </h1>
          <p className="text-slate-500 font-bold text-xs uppercase tracking-[0.3em] mt-2">Intelligence Interface v2.0</p>
        </div>

        {/* Login Card */}
        <div className="glass-card p-10 backdrop-blur-3xl border-white/10 shadow-2xl">
          <div className="mb-8 text-center md:text-left">
            <h2 className="text-xl font-bold text-white mb-2">Initialize Session</h2>
            <p className="text-slate-500 text-sm font-medium italic">Enter your neural identity to access your isolated intelligence bank.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Access Protocol (Identity/ID)</label>
              <div className="relative group">
                <User className="h-5 w-5 text-slate-600 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-indigo transition-colors" />
                <input
                  type="text"
                  value={identity}
                  onChange={(e) => setIdentity(e.target.value)}
                  placeholder="e.g. user123 or julie"
                  className="input-field pl-12 py-4"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-xs font-bold text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-4 text-lg group/btn disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="flex items-center justify-center gap-3">
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Authorizing...</span>
                  </>
                ) : (
                  <>
                    <span>Direct Access</span>
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </div>
            </button>
          </form>

          <div className="mt-10 pt-8 border-t border-white/5 flex flex-col items-center gap-4">
            <div className="flex items-center gap-2 text-[10px] font-bold text-slate-600 uppercase tracking-widest">
              <Sparkles className="h-3 w-3" />
              <span>Isolated Data Partition Active</span>
            </div>
            <p className="text-slate-600 text-xs font-medium italic text-center">
              No password required. Access is tied to your unique identity.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
