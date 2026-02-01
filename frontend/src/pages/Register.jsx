import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { UserPlus, Mail, Lock, User, Building, ArrowRight, ShieldCheck } from 'lucide-react'

function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    fullName: '',
    company: ''
  })
  const { register, loading, error } = useAuthStore()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await register(
      formData.email,
      formData.password,
      formData.fullName,
      formData.company
    )
    if (result.success) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#0a0f1d] relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent-indigo/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-accent-emerald/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-xl relative">
        <div className="flex flex-col items-center mb-10">
          <div className="w-16 h-16 bg-accent-indigo rounded-2xl flex items-center justify-center text-white shadow-2xl shadow-indigo-500/40 mb-6 group hover:rotate-6 transition-transform">
            <ShieldCheck className="h-10 w-10" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tighter uppercase">
            Agent<span className="text-accent-indigo">Registration</span>
          </h1>
          <p className="text-slate-500 font-bold text-[10px] uppercase tracking-[0.4em] mt-2 italic">Standard Recruitment Protocol Access</p>
        </div>

        <div className="glass-card p-10 backdrop-blur-3xl border-white/10 shadow-2xl">
          <div className="mb-10 text-center">
            <h2 className="text-xl font-bold text-white mb-2">Create New Instance</h2>
            <p className="text-slate-500 text-sm font-medium italic">Join the next generation of AI-powered scouting agents.</p>
          </div>

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Full Name</label>
                <div className="relative group">
                  <User className="h-5 w-5 text-slate-600 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-indigo transition-colors" />
                  <input
                    name="fullName"
                    type="text"
                    required
                    className="input-field pl-12"
                    placeholder="John Doe"
                    value={formData.fullName}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Affiliation</label>
                <div className="relative group">
                  <Building className="h-5 w-5 text-slate-600 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-indigo transition-colors" />
                  <input
                    name="company"
                    type="text"
                    className="input-field pl-12"
                    placeholder="Organization Name"
                    value={formData.company}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Neural ID (Email)</label>
              <div className="relative group">
                <Mail className="h-5 w-5 text-slate-600 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-indigo transition-colors" />
                <input
                  name="email"
                  type="email"
                  required
                  className="input-field pl-12"
                  placeholder="agent@recruiter-ai.com"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest ml-1">Access Cipher (Password)</label>
              <div className="relative group">
                <Lock className="h-5 w-5 text-slate-600 absolute left-4 top-1/2 -translate-y-1/2 group-focus-within:text-accent-indigo transition-colors" />
                <input
                  name="password"
                  type="password"
                  required
                  className="input-field pl-12"
                  placeholder="••••••••••••"
                  value={formData.password}
                  onChange={handleChange}
                />
              </div>
            </div>

            {error && (
              <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm font-bold text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-4 text-lg group/btn mt-4"
            >
              <div className="flex items-center justify-center gap-3">
                <span>{loading ? 'Initializing Agent...' : 'Finalize Registration'}</span>
                {!loading && <UserPlus className="h-5 w-5 group-hover:scale-110 transition-transform" />}
              </div>
            </button>

            <div className="text-center mt-8">
              <Link
                to="/login"
                className="text-slate-500 hover:text-white transition-colors text-xs font-bold uppercase tracking-[0.2em] border-b border-white/5 hover:border-white py-1"
              >
                Existing Agent? Return to Base
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Register