import { Link } from "react-router-dom"

function Dashboard() {
  const recruiterId = localStorage.getItem("recruiter_id")

  return (
    <div style={{ padding: "24px" }}>
      <h1 style={{ fontSize: "24px", marginBottom: "12px" }}>
        Recruiter Dashboard
      </h1>

      <p style={{ marginBottom: "20px" }}>
        Logged in as Recruiter ID: <b>{recruiterId}</b>
      </p>

      <div style={{ display: "flex", gap: "12px" }}>
        <Link to="/run-agent">
          <button>Run AI Agent</button>
        </Link>

        <button
          onClick={() => {
            localStorage.removeItem("recruiter_id")
            window.location.href = "/login"
          }}
        >
          Logout
        </button>
      </div>
    </div>
  )
}

export default Dashboard
