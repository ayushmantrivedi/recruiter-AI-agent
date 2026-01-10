import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login() {
  console.log('Login component rendering...')
  const [recruiterId, setRecruiterId] = useState('2')
  const navigate = useNavigate()

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Setting recruiter_id to localStorage:', recruiterId)
    localStorage.setItem('recruiter_id', recruiterId)
    console.log('Navigating to dashboard...')
    navigate('/')
    // Force page reload to trigger re-render
    window.location.reload()
  }

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Recruiter AI Login</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Recruiter ID:</label>
          <input
            type="text"
            value={recruiterId}
            onChange={(e) => setRecruiterId(e.target.value)}
            placeholder="Enter recruiter ID"
          />
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  )
}

export default Login